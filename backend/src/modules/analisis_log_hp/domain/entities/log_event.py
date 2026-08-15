"""Entidades de dominio: evento de log y evento enriquecido con catálogo."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LogEvent:
    type: str  # ERROR | WARNING | INFO
    code: str
    timestamp: datetime
    counter: int
    firmware: str | None
    help_reference: str | None


@dataclass(frozen=True)
class EnrichedEvent:
    type: str
    code: str
    timestamp: datetime
    counter: int
    firmware: str | None
    help_reference: str | None
    code_severity: str | None = None
    code_description: str | None = None
    code_solution_url: str | None = None
    code_solution_content: str | None = None
