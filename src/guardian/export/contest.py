import json
import os
import shutil
import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

class MetaInfo(BaseModel):
    topic: str = Field(default="TOPIC", description="TOPIC(불법광고)")
    entry_url: str = Field(description="입력값으로 전달받은 진입 URL")
    started_at: str = Field(description="탐지 시작(URL 입력/탐지) 시각(ISO 8601)")
    finished_at: str = Field(description="탐지 완료 시각(ISO 8601)")
    elapsed_sec: float = Field(description="탐지 시작부터 탐지 완료까지의 총 소요시간(초)")
    tool_version: Optional[str] = Field(default="0.1.0", description="제출 도구의 버전 문자열")

class Finding(BaseModel):
    id: str = Field(description="항목 고유 식별자, 파일 내 중복 불가(예: f_001)")
    url: str = Field(description="검출 항목이 존재하는 페이지의 전체 URL")
    is_violation: bool = Field(description="위반 여부 (예: true)")
    location: str = Field(description="웹페이지에서 불법광고가 검출된 요소의 위치")
    evidence_text: str = Field(description="검출 근거가 되는 원문 텍스트(정규화 전 원본 그대로)")
    normalized_text: Optional[str] = Field(default=None, description="정규화 텍스트")
    technique: str = Field(description="은닉 기법 코드")
    extra_finding: Optional[str] = Field(default=None, description="추가 개발 제안 필드 (선택)")
    screenshot_path: Optional[str] = Field(default=None, description="증거 스크린샷 경로")

class ResultExport(BaseModel):
    meta: MetaInfo
    findings: List[Finding]

def validate_result_dict(data: dict):
    """
    대회 규격에 맞는 데이터 구조인지 자체 검증합니다.
    """
    if not isinstance(data, dict):
        raise ValueError("Root must be an object")
    if "meta" not in data or not isinstance(data["meta"], dict):
        raise ValueError("Missing or invalid 'meta'")
    meta = data["meta"]
    for req in ["topic", "entry_url", "started_at", "finished_at", "elapsed_sec"]:
        if req not in meta:
            raise ValueError(f"Missing meta field: {req}")
    if not isinstance(meta["elapsed_sec"], (int, float)):
        raise ValueError("elapsed_sec must be numeric")
        
    if "findings" not in data or not isinstance(data["findings"], list):
        raise ValueError("Missing or invalid 'findings'")
    for idx, f in enumerate(data["findings"]):
        if not isinstance(f, dict):
            raise ValueError(f"Finding item {idx} must be an object")
        for req in ["id", "url", "is_violation", "location", "evidence_text", "technique"]:
            if req not in f:
                raise ValueError(f"Finding item {idx} missing field: {req}")

def archive_previous_result(output_path: str):
    if os.path.exists(output_path):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_name = os.path.dirname(output_path)
        base_name = os.path.basename(output_path)
        name, ext = os.path.splitext(base_name)
        
        archive_dir = os.path.join(dir_name, "archives")
        os.makedirs(archive_dir, exist_ok=True)
        
        archive_path = os.path.join(archive_dir, f"{name}_{ts}{ext}")
        shutil.copy2(output_path, archive_path)

def save_result(result: ResultExport, output_path: str):
    archive_previous_result(output_path)
    
    json_str = result.model_dump_json(exclude_none=True, indent=2)
    data = json.loads(json_str)
    
    # 구조 검증
    try:
        validate_result_dict(data)
    except Exception as e:
        print(f"Schema validation warning: {e}")
        output_path = output_path + ".fallback.json"
        
    temp_path = output_path + ".tmp"
    
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(json_str)
        
    # Atomic replace
    os.replace(temp_path, output_path)
