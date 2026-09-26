from urllib.parse import urlparse, urlunparse
import urllib.robotparser

class UrlPolicy:
    def __init__(self, entry_url: str):
        self.entry_url = entry_url
        self.entry_domain = urlparse(entry_url).netloc
        self.rp = urllib.robotparser.RobotFileParser()
        self.robots_loaded = False
        
    def load_robots(self):
        if self.robots_loaded:
            return
        parsed = urlparse(self.entry_url)
        if parsed.scheme in ["http", "https"]:
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            self.rp.set_url(robots_url)
            try:
                self.rp.read()
            except:
                pass
        self.robots_loaded = True
        
    def is_allowed(self, url: str, user_agent: str = "*") -> bool:
        """
        Check if URL is within allowed crawl scope (same origin) and respects robots.txt.
        """
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https", "file"]:
            return False
            
        if parsed.scheme == "file":
            return True
            
        if parsed.netloc != self.entry_domain:
            return False
            
        self.load_robots()
        
        # Check robots.txt
        if not self.rp.can_fetch(user_agent, url):
            return False
            
        return True
        
    def canonicalize(self, url: str) -> str:
        """
        Remove fragments from URL for deduplication.
        """
        parsed = urlparse(url)
        return urlunparse(parsed._replace(fragment=""))
