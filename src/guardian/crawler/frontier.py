import asyncio
from collections import deque
from guardian.crawler.url_policy import UrlPolicy
from typing import Optional, Set, Tuple

class CrawlFrontier:
    def __init__(self, entry_url: str, max_depth: int = 6, max_pages: int = 500):
        self.policy = UrlPolicy(entry_url)
        self.max_depth = max_depth
        self.max_pages = max_pages
        
        self.queue = deque([(entry_url, 0)]) # (url, depth)
        self.visited: Set[str] = set()
        self.scanned_count = 0
        
    def add_url(self, url: str, depth: int):
        canonical_url = self.policy.canonicalize(url)
        if canonical_url not in self.visited and self.policy.is_allowed(canonical_url):
            if depth <= self.max_depth:
                self.queue.append((canonical_url, depth))
                
    def get_next(self) -> Optional[Tuple[str, int]]:
        if self.scanned_count >= self.max_pages:
            return None
            
        while self.queue:
            url, depth = self.queue.popleft()
            if url not in self.visited:
                self.visited.add(url)
                self.scanned_count += 1
                return url, depth
                
        return None
