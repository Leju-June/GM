import unicodedata

def normalize_homoglyphs(text: str) -> str:
    """
    Normalize confusable characters (like fullwidth Latin) to basic Latin or Korean.
    Example: ｍｅｇａ－ＢＥＴ -> mega-BET
    """
    # NFKC normalizes fullwidth characters to standard width.
    return unicodedata.normalize('NFKC', text)
