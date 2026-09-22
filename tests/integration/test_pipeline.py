import pytest
import os
import asyncio
from guardian.crawler.navigation import Crawler

def get_fixture_url(filename):
    path = os.path.join(os.path.dirname(__file__), "..", "fixtures", filename)
    return f"file:///{path.replace(chr(92), '/')}"

@pytest.mark.asyncio
async def test_vertical_slice():
    url = get_fixture_url("test_page.html")
    crawler = Crawler(url)
    await crawler.start()
    findings = await crawler.run()
    await crawler.close()
    
    techniques_found = set(f["technique"] for f in findings)
    assert "JAMO" in techniques_found
    assert "HOMOGLYPH" in techniques_found
    assert "TRANSPARENT" in techniques_found
    assert "OFFSCREEN" in techniques_found

@pytest.mark.asyncio
async def test_iframe_extraction():
    url = get_fixture_url("test_page_with_iframe.html")
    crawler = Crawler(url)
    await crawler.start()
    findings = await crawler.run()
    await crawler.close()
    
    assert len(findings) > 0
    # Location should contain '>>>' denoting frame boundary
    assert ">>>" in findings[0]["location"]
    # Technique should be TRANSPARENT due to opacity: 0
    assert findings[0]["technique"] == "TRANSPARENT"
