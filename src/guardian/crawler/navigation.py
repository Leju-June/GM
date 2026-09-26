from playwright.async_api import async_playwright, Page, Frame, Route
import os
import datetime
import asyncio
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse
from guardian.extraction.models import ExtractedNode
from guardian.detection.attribution import analyze_node
from guardian.crawler.frontier import CrawlFrontier

# Helper to check if IP is private (simple SSRF protection)
def is_private_ip(ip: str) -> bool:
    if ip.startswith("127.") or ip.startswith("10.") or ip.startswith("192.168."):
        return True
    if ip.startswith("172."):
        # 172.16.x.x - 172.31.x.x
        parts = ip.split(".")
        if len(parts) == 4 and parts[1].isdigit():
            second = int(parts[1])
            if 16 <= second <= 31:
                return True
    return False

class Crawler:
    def __init__(self, entry_url: str, settings: dict = None, storage = None):
        self.playwright = None
        self.browser = None
        
        self.settings = settings or {}
        max_depth = self.settings.get("max_depth", 6)
        max_pages = self.settings.get("max_pages", 500)
        self.concurrency = self.settings.get("concurrency", 2)
        self.timeout_sec = self.settings.get("timeout_sec", 30)
        self.global_timeout = 25 * 60 # 25 minutes limit
        
        self.frontier = CrawlFrontier(entry_url, max_depth=max_depth, max_pages=max_pages)
        self.all_findings = []
        self.storage = storage
        
        self.iframes_count = 0
        self.fails_count = 0

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def _route_interceptor(self, route: Route):
        # SSRF Protection: Block navigation to private IPs if they are not the entry URL
        url = route.request.url
        parsed = urlparse(url)
        hostname = parsed.hostname
        if hostname and is_private_ip(hostname):
            # Only block if it's not the entry_url's hostname
            entry_hostname = urlparse(self.frontier.policy.entry_url).hostname
            if hostname != entry_hostname:
                await route.abort("accessdenied")
                return
        await route.continue_()
            
    async def worker(self, context, worker_id):
        page = await context.new_page()
        await page.route("**/*", self._route_interceptor)
        
        while True:
            next_item = self.frontier.get_next()
            if not next_item:
                break
                
            url, depth = next_item
            
            try:
                # 1 origin per navigation (already handled by same-domain policy, but here we process the page)
                findings, links = await self._scan_page(page, url)
                self.all_findings.extend(findings)
                
                # DB logging
                if self.storage:
                    self.storage.record_page_status(url, "success", depth)
                    for f in findings:
                        self.storage.add_finding(f.get("id", ""), f["url"], f["location"], f["evidence_text"], f["technique"], f)
                
                # Add discovered links
                for link in links:
                    self.frontier.add_url(link, depth + 1)
            except Exception as e:
                self.fails_count += 1
                if self.storage:
                    self.storage.record_page_status(url, "failed", depth, str(e))
                
        await page.close()

    async def run(self):
        context = await self.browser.new_context()
        
        async def run_workers():
            tasks = []
            for i in range(self.concurrency):
                tasks.append(asyncio.create_task(self.worker(context, i)))
            await asyncio.gather(*tasks)
            
        try:
            # 25-minute global timeout
            await asyncio.wait_for(run_workers(), timeout=self.global_timeout)
        except asyncio.TimeoutError:
            print("Global 25-minute timeout reached. Stopping crawl.")
            if self.storage:
                self.storage.set_meta("timeout_reached", "true")
        except Exception as e:
            print(f"Crawler run failed: {e}")
            
        await context.close()
        return self.all_findings

    async def _scan_page(self, page: Page, url: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        findings = []
        links = []
        
        # Load page with stabilization (networkidle + wait)
        # We use a slightly smaller timeout than the worker setting for goto
        goto_timeout = (self.timeout_sec * 1000) * 0.8 
        await page.goto(url, wait_until="networkidle", timeout=goto_timeout)
        
        # Trigger lazy load by scrolling
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000) # Give it a moment to load content after scroll
        
        script_path = os.path.join(os.path.dirname(__file__), '..', 'extraction', 'dom_extract.js')
        with open(script_path, 'r', encoding='utf-8') as f:
            extract_script = f.read()

        frames = page.frames
        for frame in frames:
            self.iframes_count += 1
            frame_chain = await self._build_frame_chain(frame)
            
            try:
                raw_nodes = await frame.evaluate(f"() => {{ {extract_script}; return extractNodes(); }}")
                
                for raw_node in raw_nodes:
                    node = ExtractedNode(
                        text=raw_node["text"],
                        original_whitespace=raw_node["text"],
                        tag_name=raw_node["tag_name"],
                        classes=raw_node["classes"],
                        attributes={},
                        computed_styles=raw_node["computed_styles"],
                        bounding_rect=raw_node["bounding_rect"],
                        page_url=url,
                        frame_chain=frame_chain,
                        extraction_time=datetime.datetime.now().isoformat()
                    )
                    
                    techniques, normalized_text = analyze_node(node)
                    
                    location = raw_node["location_selector"]
                    if frame_chain:
                        chain_str = " >>> ".join(frame_chain)
                        location = f"{chain_str} >>> {location}"
                        
                    for tech in techniques:
                        findings.append({
                            "url": url,
                            "location": location,
                            "evidence_text": node.text,
                            "normalized_text": normalized_text,
                            "technique": tech
                        })
            except Exception as frame_e:
                pass # Frame extraction failed (e.g., cross-origin block)
        
        raw_links = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)")
        links.extend(raw_links)
        
        # Evidence Screenshot Capture
        if findings:
            try:
                parsed_url = urlparse(url)
                domain = parsed_url.hostname or "unknown"
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                import uuid
                evidence_id = uuid.uuid4().hex[:8]
                screenshot_filename = f"{domain}_{ts}_{evidence_id}.png"
                
                # Assume evidence goes to output_dir/evidence
                evidence_dir = "evidence"
                if self.settings and self.settings.get("output_path"):
                    evidence_dir = os.path.join(os.path.dirname(self.settings["output_path"]), "evidence")
                os.makedirs(evidence_dir, exist_ok=True)
                
                screenshot_path = os.path.join(evidence_dir, screenshot_filename)
                await page.screenshot(path=screenshot_path, full_page=True)
                
                # Attach screenshot path to all findings from this page
                for f in findings:
                    f['screenshot_path'] = screenshot_path
            except Exception as e:
                print(f"Failed to capture screenshot for {url}: {e}")
                
        return findings, links
        
    async def _build_frame_chain(self, frame: Frame) -> List[str]:
        chain = []
        current = frame
        while current.parent_frame:
            try:
                frame_el = await current.frame_element()
                sel = await frame_el.evaluate("""(el) => {
                    let sel = 'iframe';
                    const src = el.getAttribute('src');
                    if (src) {
                        sel += `[src="${src}"]`;
                    }
                    const parent = el.parentElement;
                    if (parent) {
                        // find siblings with same tag and src to add nth-of-type if needed
                        const siblings = Array.from(parent.children).filter(c => 
                            c.tagName === 'IFRAME' && c.getAttribute('src') === src
                        );
                        if (siblings.length > 1) {
                            sel += `:nth-of-type(${siblings.indexOf(el) + 1})`;
                        }
                    }
                    return sel;
                }""")
                chain.insert(0, sel)
            except Exception:
                chain.insert(0, f'iframe[src="{current.url}"]')
            current = current.parent_frame
        return chain
