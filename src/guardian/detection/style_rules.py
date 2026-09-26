from typing import Dict, Any

def check_transparent(computed_styles: Dict[str, str]) -> bool:
    """
    Check for TRANSPARENT technique:
    - effective_opacity: near 0
    - color: transparent
    - color matches effective_background_color
    """
    opacity = computed_styles.get("effective_opacity", computed_styles.get("opacity", "1"))
    try:
        if float(opacity) <= 0.01:
            return True
    except ValueError:
        pass
        
    color = computed_styles.get("color", "").replace(" ", "").lower()
    if color == "transparent" or color == "rgba(0,0,0,0)":
        return True
        
    bg_color = computed_styles.get("effective_background_color", "").replace(" ", "").lower()
    if color and bg_color and color == bg_color and color != "rgba(0,0,0,0)":
        return True
        
    return False

def check_offscreen(computed_styles: Dict[str, str]) -> bool:
    """
    Check for OFFSCREEN technique:
    - display: none
    - visibility: hidden
    - font-size: 0px or 1px
    - left/top: -9999px (large negative positioning)
    - text-indent: -9999px
    - clip: rect(...)
    """
    display = computed_styles.get("display", "")
    if display == "none":
        return True
        
    visibility = computed_styles.get("visibility", "")
    if visibility == "hidden":
        return True
        
    font_size = computed_styles.get("font-size", "")
    if font_size in ["0px", "1px"]:
        return True
        
    position = computed_styles.get("position", "")
    if position == "absolute" or position == "fixed":
        left = computed_styles.get("left", "")
        top = computed_styles.get("top", "")
        
        # Check for large negative positioning
        if "-99" in left or "-99" in top: 
            return True
            
        clip = computed_styles.get("clip", "")
        if "rect" in clip and ("0px" in clip or "1px" in clip):
            return True
            
    text_indent = computed_styles.get("text-indent", "")
    if "-99" in text_indent:
        return True
            
    return False
