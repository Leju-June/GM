import unicodedata

# Initial consonants
CHOSEONG = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
# Medial vowels
JUNGSEONG = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
# Final consonants
JONGSEONG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

def reconstruct_jamo(text: str) -> str:
    """
    Attempt to reconstruct scattered Jamo into Hangul syllables.
    Example: ㅋㅏㅈㅣㄴㅗ -> 카지노
    """
    result = []
    i = 0
    n = len(text)
    
    while i < n:
        char = text[i]
        
        if char in CHOSEONG:
            cho = CHOSEONG.index(char)
            # Check for vowel
            if i + 1 < n and text[i+1] in JUNGSEONG:
                jung = JUNGSEONG.index(text[i+1])
                jong = 0
                
                # Check for final consonant
                if i + 2 < n and text[i+2] in JONGSEONG and text[i+2] != '':
                    # Ensure it's not the start of a new syllable
                    # A final consonant followed by a vowel is actually the initial of the next syllable
                    if i + 3 < n and text[i+3] in JUNGSEONG:
                        pass # It's a choseong of the next block
                    else:
                        jong = JONGSEONG.index(text[i+2])
                        
                syllable_code = 0xAC00 + (cho * 21 * 28) + (jung * 28) + jong
                result.append(chr(syllable_code))
                
                i += 2 if jong == 0 else 3
                continue
                
        result.append(char)
        i += 1
        
    return "".join(result)
