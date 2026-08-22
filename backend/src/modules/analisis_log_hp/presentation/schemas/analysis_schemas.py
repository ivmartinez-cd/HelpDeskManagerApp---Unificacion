from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from src.modules.analisis_log_hp.domain.entities.incident import Incident
from src.modules.analisis_log_hp.domain.entities.log_event import EnrichedEvent
from src.modules.analisis_log_hp.domain.services.log_parser import ParserError


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

    @classmethod
    def from_entity(cls, e: EnrichedEvent) -> LogEventSchema:
        return cls(
            type=e.type, code=e.code, timestamp=e.timestamp, counter=e.counter,
            firmware=e.firmware, help_reference=e.help_reference,
            code_severity=e.code_severity, code_description=e.code_description,
            code_solution_url=e.code_solution_url,
        )


class ParserErrorSchema(BaseModel):
    line_number: int
    raw_line: str
    reason: str

    @classmethod
    def from_entity(cls, e: ParserError) -> ParserErrorSchema:
        return cls(line_number=e.line_number, raw_line=e.raw_line, reason=e.reason)


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
    code_description: str | None = None

    @classmethod
    def from_entity(cls, i: Incident) -> IncidentSchema:
        return cls(
            id=i.id, code=i.code, classification=i.classification,
            severity=i.severity, severity_weight=i.severity_weight,
            occurrences=i.occurrences, start_time=i.start_time,
            end_time=i.end_time, counter_range=list(i.counter_range),
            sds_link=i.sds_link, code_description=i.code_description,
        )


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
