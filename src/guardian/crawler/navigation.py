from playwright.async_api import async_playwright, Page, Frame
import os
import datetime
from typing import List, Dict, Any, Tuple
from guardian.extraction.models import ExtractedNode
from guardian.detection.attribution import analyze_node
from guardian.crawler.frontier import CrawlFrontier

class Crawler:
    def __init__(self, entry_url: str):
        self.playwright = None
        self.browser = None
        self.frontier = CrawlFrontier(entry_url)
        self.all_findings = []

    async def start(self):
        self.playwright = await async_playwright().start()
        # Ephemeral context, no user cookies
        self.browser = await self.playwright.chromium.launch(headless=True)

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def run(self):
        context = await self.browser.new_context()
        page = await context.new_page()
        
        while True:
            next_item = self.frontier.get_next()
            if not next_item:
                break
            url, depth = next_item
            
            print(f"[{self.frontier.scanned_count}] Scanning (depth {depth}): {url}")
            try:
                findings, links = await self._scan_page(page, url)
                self.all_findings.extend(findings)
                
                # Add discovered links
                for link in links:
                    self.frontier.add_url(link, depth + 1)
            except Exception as e:
                print(f"Error scanning {url}: {e}")
                
        await context.close()
        return self.all_findings

    async def _scan_page(self, page: Page, url: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        findings = []
        links = []
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(1000) # Basic stabilization

            script_path = os.path.join(os.path.dirname(__file__), '..', 'extraction', 'dom_extract.js')
            with open(script_path, 'r', encoding='utf-8') as f:
                extract_script = f.read()

            # Process main page and all iframes
            frames = page.frames
            for frame in frames:
                frame_chain = self._build_frame_chain(frame)
                
                try:
                    # Inject and run extraction script in frame
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
                        
                        techniques = analyze_node(node)
                        
                        # Format location properly for iframes
                        location = raw_node["location_selector"]
                        if frame_chain:
                            # prefix with iframe src chain
                            chain_str = " >>> ".join([f'iframe[src="{src}"]' for src in frame_chain])
                            location = f"{chain_str} >>> {location}"
                            
                        for tech in techniques:
                            findings.append({
                                "url": url,
                                "location": location,
                                "evidence_text": node.text,
                                "technique": tech
                            })
                except Exception as frame_e:
                    # Some cross-origin frames might block evaluation if web security is strictly enforced
                    # Though Playwright typically can evaluate if properly attached.
                    print(f"Could not extract from frame {frame.url}: {frame_e}")
            
            # Extract links
            raw_links = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)")
            links.extend(raw_links)
            
        except Exception as e:
            print(f"Navigation error: {e}")
            
        return findings, links
        
    def _build_frame_chain(self, frame: Frame) -> List[str]:
        chain = []
        current = frame
        while current.parent_frame:
            # We record the src or url of the iframe
            # To be accurate to the spec: iframe[src="ABSOLUTE_URL"]
            # We use current.url as the resolved absolute URL
            chain.insert(0, current.url)
            current = current.parent_frame
        return chain
