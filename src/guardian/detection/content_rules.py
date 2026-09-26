import os
import ahocorasick
from guardian.normalization.hangul import reconstruct_jamo
from guardian.normalization.confusables import normalize_homoglyphs
from guardian.normalization.provenance import NormalizedText

class ContentDetector:
    def __init__(self):
        self.automaton = ahocorasick.Automaton()
        self.whitelist = []
        self._load_rules()
        
    def _load_rules(self):
        base_dir = os.path.dirname(__file__)
        rules_dir = os.path.join(base_dir, '..', 'resources', 'rules')
        
        keywords_path = os.path.join(rules_dir, 'keywords.txt')
        context_path = os.path.join(rules_dir, 'context_rules.txt')
        
        # Load Keywords
        if os.path.exists(keywords_path):
            with open(keywords_path, 'r', encoding='utf-8') as f:
                for idx, line in enumerate(f):
                    key = line.strip()
                    if key:
                        self.automaton.add_word(key, (idx, key))
                        self.automaton.add_word(key.lower(), (idx, key.lower()))
        self.automaton.make_automaton()
        
        # Load Whitelist Contexts
        if os.path.exists(context_path):
            with open(context_path, 'r', encoding='utf-8') as f:
                for line in f:
                    ctx = line.strip()
                    if ctx:
                        self.whitelist.append(ctx.lower())
                        
    def _is_whitelisted(self, text: str) -> bool:
        lower_text = text.lower()
        for w in self.whitelist:
            if w in lower_text:
                return True
        return False
        
    def detect_jamo_evasion(self, original_text: str) -> bool:
        if self._is_whitelisted(original_text):
            return False
            
        original_matches = list(self.automaton.iter(original_text.lower()))
        if original_matches:
            return False
            
        norm = NormalizedText(original_text)
        reconstructed = reconstruct_jamo(norm)
        
        if self._is_whitelisted(reconstructed.text):
            return False
            
        reconstructed_matches = list(self.automaton.iter(reconstructed.text.lower()))
        return len(reconstructed_matches) > 0
        
    def detect_homoglyph_evasion(self, original_text: str) -> bool:
        if self._is_whitelisted(original_text):
            return False
            
        original_matches = list(self.automaton.iter(original_text.lower()))
        if original_matches:
            return False
            
        norm = NormalizedText(original_text)
        normalized = normalize_homoglyphs(norm)
        
        if self._is_whitelisted(normalized.text):
            return False
            
        normalized_matches = list(self.automaton.iter(normalized.text.lower()))
        return len(normalized_matches) > 0
        
    def check_suspicious_content(self, text: str) -> tuple[bool, str, str]:
        """Check if any suspicious keywords are in the text after full normalization"""
        if self._is_whitelisted(text):
            return False, "", ""
            
        norm = NormalizedText(text)
        step1 = reconstruct_jamo(norm)
        step2 = normalize_homoglyphs(step1)
        
        if self._is_whitelisted(step2.text):
            return False, "", ""
            
        matches = list(self.automaton.iter(step2.text.lower()))
        if matches:
            return True, matches[0][1][1], step2.text
            
        return False, "", ""
