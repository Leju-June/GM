from typing import List, Tuple
from guardian.extraction.models import ExtractedNode
from guardian.detection.style_rules import check_transparent, check_offscreen
from guardian.detection.content_rules import ContentDetector

detector = ContentDetector()

def analyze_node(node: ExtractedNode) -> List[str]:
    """
    Returns a list of technique codes found in the given node.
    Codes: "HOMOGLYPH", "JAMO", "TRANSPARENT", "OFFSCREEN"
    """
    techniques = []
    
    # 1. Check style evations
    if check_transparent(node.computed_styles):
        # Even if transparent, we should verify it has suspicious content
        if detector.check_suspicious_content(node.text):
            techniques.append("TRANSPARENT")
            
    if check_offscreen(node.computed_styles):
        if detector.check_suspicious_content(node.text):
            techniques.append("OFFSCREEN")
            
    # 2. Check text transformation evasions
    # Note: If it's already hidden via CSS, it might ALSO be transformed.
    if detector.detect_jamo_evasion(node.text):
        techniques.append("JAMO")
        
    if detector.detect_homoglyph_evasion(node.text):
        techniques.append("HOMOGLYPH")
        
    return techniques
