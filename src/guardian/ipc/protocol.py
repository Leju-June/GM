import json
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class IpcMessage(BaseModel):
    type: str
    payload: Dict[str, Any]
    
def encode_message(msg_type: str, payload: dict) -> str:
    msg = IpcMessage(type=msg_type, payload=payload)
    return msg.model_dump_json(exclude_none=True)
    
def decode_message(line: str) -> Optional[IpcMessage]:
    try:
        data = json.loads(line)
        return IpcMessage(**data)
    except Exception:
        return None
