"""Manual de servicio CPMD (PDF) asociado a una familia de modelos HP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CpmdManual:
    id: int
    keywords: list[str]
    label: str
    filename: str
    uploaded_at: datetime
