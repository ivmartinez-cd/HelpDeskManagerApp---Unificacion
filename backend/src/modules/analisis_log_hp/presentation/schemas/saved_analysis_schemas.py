from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from src.modules.analisis_log_hp.presentation.schemas.analysis_schemas import IncidentSchema


class SavedAnalysisResponse(BaseModel):
    id: UUID
    name: str
    equipment_identifier: str | None
    global_severity: str
    created_at: datetime


class SavedAnalysisDetailResponse(SavedAnalysisResponse):
    incidents: list[dict[str, Any]]
    ai_diagnosis: str | None


class CreateSavedAnalysisRequest(BaseModel):
    name: str
    equipment_identifier: str | None = None
    incidents: list[IncidentSchema]
    global_severity: str
    ai_diagnosis: str | None = None


class CompareLogsRequest(BaseModel):
    logs: str


class DeviceHealthResponse(BaseModel):
    status: str
    label: str
    reason: str
    recommendation: str
    triggered_rule: str | None
    events_count: int
