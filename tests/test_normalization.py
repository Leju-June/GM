import pytest
from guardian.normalization.provenance import NormalizedText
from guardian.normalization.hangul import reconstruct_jamo
from guardian.normalization.confusables import normalize_homoglyphs

def test_jamo_reconstruction():
    # Basic
    text = NormalizedText("ㅋㅏㅈㅣㄴㅗ")
    result = reconstruct_jamo(text)
    assert result.text == "카지노"
    
    # Scattered with noise
    text2 = NormalizedText("ㅋ-ㅏ ㅈ*ㅣ ㄴ_ㅗ")
    result2 = reconstruct_jamo(text2)
    assert result2.text == "카지노"
    
    # Complex combinations
    text3 = NormalizedText("ㄱㅅ ㅗㅏ")
    result3 = reconstruct_jamo(text3)
    assert result3.text == "ㄳ ㅘ"
    
    # Ignore repetitions
    text4 = NormalizedText("ㅋㅋㅋ")
    result4 = reconstruct_jamo(text4)
    assert result4.text == "ㅋㅋㅋ"

def test_homoglyph_normalization():
    text = NormalizedText("mｅgа-BＥT") # Contains fullwidth and cyrillic 'а'
    result = normalize_homoglyphs(text)
    assert result.text == "mega-8ET"
    
    text2 = NormalizedText("lO8") # l -> 1, O -> 0, B -> 8
    result2 = normalize_homoglyphs(text2)
    assert result2.text == "108"
