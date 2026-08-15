"""Catálogo de códigos de error HP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ErrorCode:
    code: str
    severity: str | None
    description: str | None
    solution_url: str | None
    solution_content: str | None
    created_at: datetime
    updated_at: datetime
