from typing import Dict, Any, List

def check_transparent(computed_styles: Dict[str, str]) -> bool:
    """
    Check for TRANSPARENT technique:
    - opacity: 0
    - color: transparent
    """
    opacity = computed_styles.get("opacity", "1")
    try:
        if float(opacity) == 0.0:
            return True
    except ValueError:
        pass
        
    color = computed_styles.get("color", "").replace(" ", "").lower()
    if color == "transparent" or color == "rgba(0,0,0,0)":
        return True
        
    return False

def check_offscreen(computed_styles: Dict[str, str]) -> bool:
    """
    Check for OFFSCREEN technique:
    - display: none
    - font-size: 0px or 1px
    - left: -9999px (large negative positioning)
    """
    display = computed_styles.get("display", "")
    if display == "none":
        return True
        
    font_size = computed_styles.get("font-size", "")
    if font_size in ["0px", "1px"]:
        return True
        
    position = computed_styles.get("position", "")
    if position == "absolute":
        left = computed_styles.get("left", "")
        # Very basic check for large negative positioning
        if "-99" in left: 
            return True
            
    return False
