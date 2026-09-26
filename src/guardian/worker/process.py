import sys
import asyncio
from datetime import datetime
import uuid
import os
import time

# Force utf-8 encoding for IPC over stdout/stderr
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from guardian.crawler.navigation import Crawler
from guardian.export.contest import ResultExport, MetaInfo, Finding, save_result
from guardian.ipc.protocol import encode_message, decode_message
from guardian.storage.db import ScanStorage

async def read_stdin(cancel_event, crawler):
    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            break
        msg = decode_message(line)
        if msg and msg.type == "CANCEL":
            cancel_event.set()
            break

async def report_metrics(crawler, start_time_mono, cancel_event):
    while not cancel_event.is_set():
        await asyncio.sleep(1.0)
        if crawler and hasattr(crawler, 'frontier'):
            elapsed = time.monotonic() - start_time_mono
            m, s = divmod(int(elapsed), 60)
            print(encode_message("METRICS", {
                "elapsed": f"{m:02d}:{s:02d}",
                "visited": crawler.frontier.scanned_count,
                "queue": crawler.frontier.queue_size() if hasattr(crawler.frontier, 'queue_size') else 0,
                "iframes": getattr(crawler, 'iframes_count', 0),
                "fails": getattr(crawler, 'fails_count', 0)
            }), flush=True)

async def run_worker():
    line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
    if not line:
        return
        
    msg = decode_message(line)
    if not msg or msg.type != "START":
        return
        
    url = msg.payload.get("url")
    output_path = msg.payload.get("output_path", "result.json")
    settings = msg.payload.get("settings", {})
    
    # DB initialization
    db_path = output_path.replace(".json", ".db")
    storage = ScanStorage(db_path)
    storage.set_meta("entry_url", url)
    
    start_time = datetime.now()
    start_time_mono = time.monotonic()
    storage.set_meta("started_at", start_time.astimezone().isoformat())
    
    # Init crawler with settings
    crawler = Crawler(url, settings=settings, storage=storage)
    await crawler.start()
    
    cancel_event = asyncio.Event()
    
    stdin_task = asyncio.create_task(read_stdin(cancel_event, crawler))
    metrics_task = asyncio.create_task(report_metrics(crawler, start_time_mono, cancel_event))
    
    print(encode_message("STARTED", {"url": url}), flush=True)
    
    run_task = asyncio.create_task(crawler.run())
    
    done, pending = await asyncio.wait(
        [run_task, asyncio.create_task(cancel_event.wait())],
        return_when=asyncio.FIRST_COMPLETED
    )
    
    if cancel_event.is_set():
        run_task.cancel()
        print(encode_message("ERROR", {"message": "Scan cancelled by user."}), flush=True)
        try:
            await crawler.close()
        except:
            pass
        return
        
    # Get findings from crawler. But we also have them in storage.
    try:
        findings_raw = run_task.result()
    except Exception as e:
        print(encode_message("ERROR", {"message": f"Crawler failed: {e}"}), flush=True)
        findings_raw = []
    
    stdin_task.cancel()
    metrics_task.cancel()
    
    await crawler.close()
    
    end_time = datetime.now()
    elapsed = time.monotonic() - start_time_mono
    storage.set_meta("finished_at", end_time.astimezone().isoformat())
    storage.set_meta("elapsed_sec", str(elapsed))
    
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
                id=f.get('id', f"f_{uuid.uuid4().hex[:8]}"),
                url=f['url'],
                is_violation=True,
                location=f['location'],
                evidence_text=f['evidence_text'],
                normalized_text=f.get('normalized_text'),
                technique=f['technique'],
                screenshot_path=f.get('screenshot_path')
            )
            findings.append(finding)
            
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
