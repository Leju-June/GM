from typing import List, Tuple

class NormalizedText:
    """
    Tracks text transformations to preserve mapping back to the original source string.
    """
    def __init__(self, text: str, offsets: List[List[int]] = None):
        self.text = text
        # offsets[i] = list of original indices that map to text[i]
        if offsets is None:
            self.offsets = [[i] for i in range(len(text))]
        else:
            self.offsets = offsets
            
    def __str__(self):
        return self.text
        
    def __len__(self):
        return len(self.text)
        
    def get_original_indices(self, start: int, end: int) -> List[int]:
        """
        Get all original indices for a slice of the normalized text.
        """
        orig_indices = []
        for i in range(start, end):
            if i < len(self.offsets):
                orig_indices.extend(self.offsets[i])
        return sorted(list(set(orig_indices)))
        
    def get_original_substring(self, original_text: str, start: int, end: int) -> str:
        """
        Extract the original substring corresponding to a normalized slice.
        """
        indices = self.get_original_indices(start, end)
        if not indices:
            return ""
        min_idx, max_idx = min(indices), max(indices)
        return original_text[min_idx:max_idx+1]
