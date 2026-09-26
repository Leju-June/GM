import pytest
from guardian.detection.style_rules import check_transparent, check_offscreen
from guardian.detection.content_rules import ContentDetector

def test_check_transparent():
    # Exactly same color
    assert check_transparent({
        "color": "rgb(255, 255, 255)",
        "effective_background_color": "rgb(255, 255, 255)",
        "opacity": "1"
    }) == True
    
    # Zero effective opacity
    assert check_transparent({
        "color": "rgb(0, 0, 0)",
        "effective_background_color": "rgb(255, 255, 255)",
        "effective_opacity": "0"
    }) == True
    
    # Visible
    assert check_transparent({
        "color": "rgb(0, 0, 0)",
        "effective_background_color": "rgb(255, 255, 255)",
        "effective_opacity": "1"
    }) == False

def test_check_offscreen():
    # Display none
    assert check_offscreen({"display": "none"}) == True
    
    # Indent
    assert check_offscreen({"text-indent": "-9999px"}) == True
    
    # Clip
    assert check_offscreen({"position": "absolute", "clip": "rect(1px, 1px, 1px, 1px)"}) == True
    
    # Normal
    assert check_offscreen({"display": "block", "position": "relative"}) == False

def test_content_detector():
    detector = ContentDetector()
    # Add some dummy rules for testing if files aren't loaded properly
    detector.automaton.add_word("카지노", (0, "카지노"))
    detector.automaton.add_word("mega-8et", (1, "mega-8et"))
    detector.automaton.make_automaton()
    detector.whitelist = ["도박문제 전문상담"]
    
    # Direct hit
    is_suspicious, match, _ = detector.check_suspicious_content("여기 카지노 사이트입니다.")
    assert is_suspicious == True
    
    # Whitelisted context
    is_suspicious, match, _ = detector.check_suspicious_content("도박문제 전문상담은 1336 카지노 출입 금지")
    assert is_suspicious == False
    
    # Jamo Evasion
    assert detector.detect_jamo_evasion("ㅋ.ㅏ.ㅈ.ㅣ.ㄴ.ㅗ") == True
    
    # Homoglyph Evasion
    assert detector.detect_homoglyph_evasion("mｅgа-bＥt") == True
