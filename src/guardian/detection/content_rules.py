import ahocorasick
from guardian.normalization.hangul import reconstruct_jamo
from guardian.normalization.confusables import normalize_homoglyphs

# Some placeholder keywords from the spec
SUSPICIOUS_KEYWORDS = [
    "카지노",
    "먹튀검증",
    "안전놀이터",
    "첫충",
    "무료 슬롯",
    "LUCKY7",
    "mega-BET"
]

class ContentDetector:
    def __init__(self):
        self.automaton = ahocorasick.Automaton()
        for idx, key in enumerate(SUSPICIOUS_KEYWORDS):
            self.automaton.add_word(key, (idx, key))
        self.automaton.make_automaton()
        
    def detect_jamo_evasion(self, original_text: str) -> bool:
        # Check if original text doesn't match, but reconstructed does
        original_matches = list(self.automaton.iter(original_text))
        if original_matches:
            return False # Not using Jamo evasion if original already matches
            
        reconstructed = reconstruct_jamo(original_text)
        reconstructed_matches = list(self.automaton.iter(reconstructed))
        return len(reconstructed_matches) > 0
        
    def detect_homoglyph_evasion(self, original_text: str) -> bool:
        original_matches = list(self.automaton.iter(original_text))
        if original_matches:
            return False
            
        normalized = normalize_homoglyphs(original_text)
        normalized_matches = list(self.automaton.iter(normalized))
        return len(normalized_matches) > 0
        
    def check_suspicious_content(self, text: str) -> bool:
        """Check if any suspicious keywords are in the text after full normalization"""
        fully_normalized = normalize_homoglyphs(reconstruct_jamo(text))
        return len(list(self.automaton.iter(fully_normalized))) > 0
