"""Incidente (agrupación de eventos por código) y resultado de análisis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Incident:
    id: str
    code: str
    classification: str
    severity: str  # ERROR | WARNING | INFO
    severity_weight: int  # 3=ERROR, 2=WARNING, 1=INFO
    occurrences: int
    start_time: datetime
    end_time: datetime
    counter_range: tuple[int, int]
    sds_link: str | None = None
    sds_solution_content: str | None = None
    code_description: str | None = None


@dataclass(frozen=True)
class AnalysisResult:
    incidents: tuple[Incident, ...]
    global_severity: str
    events_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeviceHealth:
    status: str  # RED | YELLOW | GREEN
    label: str
    reason: str
    recommendation: str
    triggered_rule: str | None = None  # recurrence | post_repair | stable
