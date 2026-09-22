import sys
import asyncio
from datetime import datetime
import uuid

# Force utf-8 encoding for IPC over stdout/stderr
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from guardian.crawler.navigation import Crawler
from guardian.export.contest import ResultExport, MetaInfo, Finding, save_result
from guardian.ipc.protocol import encode_message, decode_message

async def run_worker():
    # Read initialization from stdin
    line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
    if not line:
        return
        
    msg = decode_message(line)
    if not msg or msg.type != "START":
        return
        
    url = msg.payload.get("url")
    output_path = msg.payload.get("output_path", "result.json")
    
    start_time = datetime.now()
    
    crawler = Crawler(url)
    await crawler.start()
    
    # Send started event
    print(encode_message("STARTED", {"url": url}), flush=True)
    
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
            finding = Finding(
                id=f"f_{uuid.uuid4().hex[:8]}",
                url=f['url'],
                is_violation=True,
                location=f['location'],
                evidence_text=f['evidence_text'],
                technique=f['technique']
            )
            findings.append(finding)
            
            # Emit finding event
            print(encode_message("FINDING", finding.model_dump()), flush=True)
            
    result = ResultExport(meta=meta, findings=findings)
    save_result(result, output_path)
    
    print(encode_message("COMPLETED", {
        "findings_count": len(findings),
        "output_path": output_path,
        "scanned_count": crawler.frontier.scanned_count
    }), flush=True)

if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(encode_message("ERROR", {"message": str(e)}), flush=True)
