import json
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
    technique: str = Field(description="은닉 기법 코드")
    extra_finding: Optional[str] = Field(default=None, description="추가 개발 제안 필드 (선택)")

class ResultExport(BaseModel):
    meta: MetaInfo
    findings: List[Finding]

def save_result(result: ResultExport, output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        # Pydantic v2
        json_str = result.model_dump_json(exclude_none=True, indent=2)
        f.write(json_str)
