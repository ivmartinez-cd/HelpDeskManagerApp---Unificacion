from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ErrorCodeSchema(BaseModel):
    code: str
    severity: str | None
    description: str | None
    solution_url: str | None
    solution_content: str | None
    created_at: datetime
    updated_at: datetime


class UpsertErrorCodeRequest(BaseModel):
    code: str
    severity: str | None = None
    description: str | None = None
    solution_url: str | None = None
