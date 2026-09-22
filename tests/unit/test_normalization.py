import pytest
from guardian.normalization.hangul import reconstruct_jamo
from guardian.normalization.confusables import normalize_homoglyphs

def test_reconstruct_jamo():
    assert reconstruct_jamo("ㅋㅏㅈㅣㄴㅗ") == "카지노"

def test_normalize_homoglyphs():
    assert normalize_homoglyphs("ｍｅｇａ－ＢＥＴ") == "mega-BET"
