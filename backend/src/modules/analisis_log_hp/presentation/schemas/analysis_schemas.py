from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class LogEventSchema(BaseModel):
    type: str
    code: str
    timestamp: datetime
    counter: int
    firmware: str | None
    help_reference: str | None
    code_severity: str | None = None
    code_description: str | None = None
    code_solution_url: str | None = None


class ParserErrorSchema(BaseModel):
    line_number: int
    raw_line: str
    reason: str


class IncidentSchema(BaseModel):
    id: str
    code: str
    classification: str
    severity: str
    severity_weight: int
    occurrences: int
    start_time: datetime
    end_time: datetime
    counter_range: list[int]
    sds_link: str | None


class AnalysisRequest(BaseModel):
    logs: str
    equipment_identifier: str | None = None


class AnalysisResponse(BaseModel):
    events: list[LogEventSchema]
    incidents: list[IncidentSchema]
    global_severity: str
    events_count: int
    codes_new: list[str]
    errors: list[ParserErrorSchema]


class ValidateRequest(BaseModel):
    logs: str


class ValidateResponse(BaseModel):
    codes_new: list[str]


class SdsExtractRequest(BaseModel):
    serial: str
    days: int = 30


class SdsExtractResponse(BaseModel):
    device_id: str
    model_name: str
    tsv: str
    help_urls_updated: int


class AiDiagnoseRequest(BaseModel):
    payload: dict[str, Any]
    model: str = "claude-sonnet-4-6"


class AiDiagnoseResponse(BaseModel):
    diagnosis: str
    tokens: dict[str, int]
    cost_usd: float


class HpCacheRefreshResponse(BaseModel):
    baseline: list[dict[str, Any]]
