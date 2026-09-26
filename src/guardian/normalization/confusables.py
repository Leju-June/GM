import unicodedata
from guardian.normalization.provenance import NormalizedText

# Basic Homoglyph mappings (Cyrillic, Greek, and Alphanumeric similarities used in obfuscation)
HOMOGLYPH_MAP = {
    # Cyrillic / Greek to Latin
    'а': 'a', 'А': 'A', 'с': 'c', 'С': 'C', 'е': 'e', 'Е': 'E',
    'о': 'o', 'О': 'O', 'р': 'p', 'Р': 'P', 'х': 'x', 'Х': 'X',
    'у': 'y', 'У': 'Y', 'ѕ': 's', 'Ѕ': 'S', 'і': 'i', 'І': 'I',
    'ј': 'j', 'Ј': 'J',
    # Alphanumeric obfuscations common in gambling/ads
    'l': '1', 'I': '1', 'O': '0', 'B': '8', 'S': '5', 'Z': '2',
    'o': '0', 'l': '1', 'i': '1'
}

def normalize_homoglyphs(norm_text: NormalizedText) -> NormalizedText:
    """
    Normalize confusable characters to basic Latin/Numbers or Hangul.
    Maintains provenance offsets.
    """
    new_chars = []
    new_offsets = []
    
    for i, char in enumerate(norm_text.text):
        # 1. NFKC normalization (handles fullwidth like ｍｅｇａ)
        nfkc_char = unicodedata.normalize('NFKC', char)
        
        for norm_c in nfkc_char:
            # 2. Homoglyph substitution
            final_c = HOMOGLYPH_MAP.get(norm_c, norm_c)
            
            new_chars.append(final_c)
            # Map this character back to the same original offsets as 'char'
            new_offsets.append(list(norm_text.offsets[i]))
            
    return NormalizedText("".join(new_chars), new_offsets)
