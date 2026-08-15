"""Snapshot de análisis guardado y eventos de telemetría."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class IncidentSummary:
    """Shape JSONB almacenado en saved_analyses.incidents."""

    code: str
    classification: str
    severity: str
    occurrences: int
    start_time: str | None
    end_time: str | None
    counter_range: list[int]
    sds_link: str | None
    last_event_time: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "classification": self.classification,
            "severity": self.severity,
            "occurrences": self.occurrences,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "counter_range": self.counter_range,
            "sds_link": self.sds_link,
            "last_event_time": self.last_event_time,
        }


@dataclass(frozen=True)
class SavedAnalysis:
    id: UUID
    name: str
    equipment_identifier: str | None
    incidents: list[dict[str, Any]]  # JSONB lista de IncidentSummary.to_dict()
    global_severity: str
    ai_diagnosis: str | None
    created_at: datetime


@dataclass(frozen=True)
class TelemetryEvent:
    device_serial: str
    saved_analysis_id: UUID | None
    code: str
    classification: str | None
    severity: str
    occurrences: int
    counter: int
    event_time: datetime
