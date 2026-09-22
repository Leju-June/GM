from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ExtractedNode(BaseModel):
    text: str
    original_whitespace: str
    element_id: Optional[str] = None
    tag_name: str
    classes: List[str]
    attributes: Dict[str, str]
    computed_styles: Dict[str, str]
    bounding_rect: Dict[str, float]
    page_url: str
    frame_chain: List[str]
    raw_src: Optional[str] = None
    resolved_src: Optional[str] = None
    extraction_time: str
