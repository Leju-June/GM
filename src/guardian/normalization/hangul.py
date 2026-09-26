import unicodedata
from guardian.normalization.provenance import NormalizedText

CHOSEONG = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
JUNGSEONG = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
JONGSEONG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

# Complex vowels/consonants composition map
COMPLEX_JAMO = {
    ('ㄱ', 'ㅅ'): 'ㄳ', ('ㄴ', 'ㅈ'): 'ㄵ', ('ㄴ', 'ㅎ'): 'ㄶ', ('ㄹ', 'ㄱ'): 'ㄺ',
    ('ㄹ', 'ㅁ'): 'ㄻ', ('ㄹ', 'ㅂ'): 'ㄼ', ('ㄹ', 'ㅅ'): 'ㄽ', ('ㄹ', 'ㅌ'): 'ㄾ',
    ('ㄹ', 'ㅍ'): 'ㄿ', ('ㄹ', 'ㅎ'): 'ㅀ', ('ㅂ', 'ㅅ'): 'ㅄ',
    ('ㅗ', 'ㅏ'): 'ㅘ', ('ㅗ', 'ㅐ'): 'ㅙ', ('ㅗ', 'ㅣ'): 'ㅚ',
    ('ㅜ', 'ㅓ'): 'ㅝ', ('ㅜ', 'ㅔ'): 'ㅞ', ('ㅜ', 'ㅣ'): 'ㅟ',
    ('ㅡ', 'ㅣ'): 'ㅢ'
}

def is_junk(char: str) -> bool:
    """Check if character is a space, dash, or other separator used to obfuscate."""
    return char.isspace() or char in "-_.*~^"

def reconstruct_jamo(norm_text: NormalizedText) -> NormalizedText:
    """
    Attempt to reconstruct scattered Jamo into Hangul syllables.
    Handles spaces, symbols, complex combinations, and provenance offsets.
    """
    text = norm_text.text
    offsets = norm_text.offsets
    
    new_chars = []
    new_offsets = []
    
    i = 0
    n = len(text)
    
    while i < n:
        char = text[i]
        
        # Keep non-jamo and junks as is if they are not part of a composition
        if char not in CHOSEONG:
            new_chars.append(char)
            new_offsets.append(list(offsets[i]))
            i += 1
            continue
            
        # We found a potential CHOSEONG. Let's look ahead for JUNGSEONG, ignoring junks.
        cho_char = char
        cho_idx = i
        cho = CHOSEONG.index(cho_char)
        
        # Look for JUNGSEONG
        j = i + 1
        jung_char = None
        jung_indices = []
        while j < n:
            if is_junk(text[j]):
                jung_indices.append(j)
                j += 1
            elif text[j] in JUNGSEONG:
                jung_char = text[j]
                jung_indices.append(j)
                break
            elif text[j] in CHOSEONG:
                # E.g. 'ㅋㅋㅋ' - don't reconstruct, it's just repetitive consonants
                break
            else:
                break
                
        if not jung_char:
            # Failed to find a vowel, just emit the consonant
            new_chars.append(char)
            new_offsets.append(list(offsets[i]))
            i += 1
            continue
            
        # Handle complex JUNGSEONG (e.g., ㅗ + ㅏ -> ㅘ)
        jung = JUNGSEONG.index(jung_char)
        
        k = j + 1
        complex_jung_indices = []
        while k < n:
            if is_junk(text[k]):
                complex_jung_indices.append(k)
                k += 1
            elif text[k] in JUNGSEONG:
                combined = COMPLEX_JAMO.get((jung_char, text[k]))
                if combined:
                    jung = JUNGSEONG.index(combined)
                    complex_jung_indices.append(k)
                    k += 1
                break
            else:
                break
                
        # Now look for JONGSEONG
        jong = 0
        jong_char = None
        jong_indices = []
        l = k
        while l < n:
            if is_junk(text[l]):
                jong_indices.append(l)
                l += 1
            elif text[l] in JONGSEONG and text[l] != '':
                # Before accepting as JONGSEONG, check if it's actually the CHOSEONG of the NEXT syllable
                # i.e., is it followed by a vowel?
                next_is_vowel = False
                m = l + 1
                while m < n:
                    if is_junk(text[m]):
                        m += 1
                    elif text[m] in JUNGSEONG:
                        next_is_vowel = True
                        break
                    else:
                        break
                
                if next_is_vowel:
                    # It belongs to the next syllable
                    break
                else:
                    jong_char = text[l]
                    jong_indices.append(l)
                    jong = JONGSEONG.index(jong_char)
                    l += 1
                    
                    # Check for complex JONGSEONG (e.g. ㄱ + ㅅ = ㄳ)
                    while l < n:
                        if is_junk(text[l]):
                            jong_indices.append(l)
                            l += 1
                        elif text[l] in JONGSEONG and text[l] != '':
                            combined_jong = COMPLEX_JAMO.get((jong_char, text[l]))
                            if combined_jong:
                                jong = JONGSEONG.index(combined_jong)
                                jong_indices.append(l)
                                l += 1
                            break
                        else:
                            break
                break
            else:
                break
                
        # Build the syllable
        syllable_code = 0xAC00 + (cho * 21 * 28) + (jung * 28) + jong
        new_chars.append(chr(syllable_code))
        
        # Combine offsets of all parts that made up this syllable
        combined_offsets = []
        combined_offsets.extend(offsets[cho_idx])
        for idx in jung_indices:
            combined_offsets.extend(offsets[idx])
        for idx in complex_jung_indices:
            combined_offsets.extend(offsets[idx])
        for idx in jong_indices:
            combined_offsets.extend(offsets[idx])
            
        new_offsets.append(sorted(list(set(combined_offsets))))
        
        # Advance i
        i = l

    return NormalizedText("".join(new_chars), new_offsets)
