import argparse
import sys
import asyncio
from datetime import datetime
import uuid

# Force utf-8 encoding for standard streams
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from guardian.crawler.navigation import Crawler
from guardian.export.contest import ResultExport, MetaInfo, Finding, save_result
from guardian.app import run_app

async def run_headless_scan(url: str, output_path: str):
    # Headless entry point logic ...
    print(f"Starting scan for {url}")
    start_time = datetime.now()
    crawler = Crawler(url)
    await crawler.start()
    findings_raw = await crawler.run()
    await crawler.close()
    
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    
    meta = MetaInfo(
        entry_url=url,
        started_at=start_time.astimezone().isoformat(),
        finished_at=end_time.astimezone().isoformat(),
        elapsed_sec=elapsed
    )
    
    findings = []
    seen = set()
    for f in findings_raw:
        key = (f['url'], f['location'], f['technique'])
        if key not in seen:
            seen.add(key)
            findings.append(Finding(
                id=f"f_{uuid.uuid4().hex[:8]}",
                url=f['url'],
                is_violation=True,
                location=f['location'],
                evidence_text=f['evidence_text'],
                technique=f['technique']
            ))
            
    result = ResultExport(meta=meta, findings=findings)
    save_result(result, output_path)
    print(f"Scan complete. Inspected {crawler.frontier.scanned_count} pages.")
    print(f"Found {len(findings)} violations. Result saved to {output_path}")
    
def main():
    parser = argparse.ArgumentParser(description="Public Web Clean Guardian")
    parser.add_argument("url", nargs="?", help="Target URL to scan (starts headless mode if provided)")
    parser.add_argument("--out", default="result.json", help="Output path for result.json")
    parser.add_argument("--worker", action="store_true", help="Run in worker mode (used by GUI IPC)")
    
    args = parser.parse_args()
    
    if args.worker:
        from guardian.worker.process import run_worker
        try:
            asyncio.run(run_worker())
        except KeyboardInterrupt:
            pass
        except Exception as e:
            from guardian.ipc.protocol import encode_message
            print(encode_message("ERROR", {"message": str(e)}), flush=True)
        sys.exit(0)
        
    if args.url:
        try:
            asyncio.run(run_headless_scan(args.url, args.out))
        except KeyboardInterrupt:
            print("Scan cancelled by user.")
            sys.exit(1)
        except Exception as e:
            print(f"Fatal error: {e}")
            sys.exit(1)
    else:
        # Run GUI
        run_app()

if __name__ == "__main__":
    main()
