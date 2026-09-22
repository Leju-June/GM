from urllib.parse import urlparse, urlunparse

class UrlPolicy:
    def __init__(self, entry_url: str):
        self.entry_url = entry_url
        self.entry_domain = urlparse(entry_url).netloc
        
    def is_allowed(self, url: str) -> bool:
        """
        Check if URL is within allowed crawl scope (same origin).
        """
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https", "file"]:
            return False
            
        # For the prototype, we only crawl the entry domain
        # If it's file:// we just allow it for testing
        if parsed.scheme == "file":
            return True
            
        return parsed.netloc == self.entry_domain
        
    def canonicalize(self, url: str) -> str:
        """
        Remove fragments from URL for deduplication.
        """
        parsed = urlparse(url)
        return urlunparse(parsed._replace(fragment=""))
