"""Fakes en memoria de los repositorios de analisis-log-hp (+ builders de entidades)
para tests de application puros; los gateways externos viven en fake_gateways.py."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from src.modules.analisis_log_hp.domain.entities.cpmd_manual import CpmdManual
from src.modules.analisis_log_hp.domain.entities.error_code import ErrorCode
from src.modules.analisis_log_hp.domain.entities.incident import Incident
from src.modules.analisis_log_hp.domain.entities.saved_analysis import (
    SavedAnalysis,
    TelemetryEvent,
)
from src.shared.presentation.schemas.pagination import Page

NOW = datetime(2026, 8, 16, 12, 0, tzinfo=UTC)


def make_error_code(
    code: str = "13.20",
    *,
    severity: str | None = "ERROR",
    description: str | None = "Atasco de papel",
    solution_url: str | None = "http://sds/13.20",
    solution_content: str | None = "<p>cache</p>",
) -> ErrorCode:
    return ErrorCode(
        code=code,
        severity=severity,
        description=description,
        solution_url=solution_url,
        solution_content=solution_content,
        created_at=NOW,
        updated_at=NOW,
    )


def make_incident(
    code: str = "13.20",
    *,
    severity: str = "ERROR",
    occurrences: int = 1,
    start: datetime = NOW,
    end: datetime = NOW,
    counter_range: tuple[int, int] = (100, 200),
) -> Incident:
    return Incident(
        id=f"{code}-{start.isoformat()}",
        code=code,
        classification=f"desc {code}",
        severity=severity,
        severity_weight={"ERROR": 3, "WARNING": 2, "INFO": 1}.get(severity, 0),
        occurrences=occurrences,
        start_time=start,
        end_time=end,
        counter_range=counter_range,
        sds_link=None,
    )


class FakeErrorCodeRepo:
    def __init__(self, codes: list[ErrorCode] | None = None, *, fail_bulk: bool = False) -> None:
        self.codes = {c.code: c for c in codes or []}
        self.fail_bulk = fail_bulk
        self.upserts: list[dict[str, Any]] = []
        self.bulk_updates: list[dict[str, dict[str, Any]]] = []

    async def get_by_code(self, code: str) -> ErrorCode | None:
        return self.codes.get(code)

    async def get_by_codes(self, codes: list[str]) -> dict[str, ErrorCode]:
        return {c: self.codes[c] for c in codes if c in self.codes}

    async def upsert(self, code: str, **fields: str | None) -> ErrorCode:
        self.upserts.append({"code": code, **fields})
        entity = make_error_code(code, **fields)  # type: ignore[arg-type]
        self.codes[code] = entity
        return entity

    async def list_page(self, page: int, size: int) -> Page[ErrorCode]:
        return Page.of(list(self.codes.values()), page=page, size=size)

    async def bulk_update_solution_urls(self, updates: dict[str, dict[str, Any]]) -> int:
        if self.fail_bulk:
            raise RuntimeError("db caída")
        self.bulk_updates.append(updates)
        return len(updates)


class FakeSavedAnalysisRepo:
    def __init__(self) -> None:
        self.rows: dict[UUID, SavedAnalysis] = {}

    def seed(
        self,
        *,
        incidents: list[dict[str, Any]] | None = None,
        equipment_identifier: str | None = "HP (SER1)",
        created_at: datetime = NOW,
        global_severity: str = "ERROR",
    ) -> SavedAnalysis:
        snap = SavedAnalysis(
            id=uuid.uuid4(),
            name="snap",
            equipment_identifier=equipment_identifier,
            incidents=incidents or [],
            global_severity=global_severity,
            ai_diagnosis=None,
            created_at=created_at,
        )
        self.rows[snap.id] = snap
        return snap

    async def create(
        self,
        name: str,
        equipment_identifier: str | None,
        incidents: list[dict[str, Any]],
        global_severity: str,
        ai_diagnosis: str | None = None,
    ) -> SavedAnalysis:
        snap = SavedAnalysis(
            id=uuid.uuid4(),
            name=name,
            equipment_identifier=equipment_identifier,
            incidents=incidents,
            global_severity=global_severity,
            ai_diagnosis=ai_diagnosis,
            created_at=NOW,
        )
        self.rows[snap.id] = snap
        return snap

    async def get_by_id(self, id: UUID) -> SavedAnalysis | None:
        return self.rows.get(id)

    async def list_page(self, page: int, size: int) -> Page[SavedAnalysis]:
        return Page.of(list(self.rows.values()), page=page, size=size)

    async def update(
        self,
        id: UUID,
        incidents: list[dict[str, Any]],
        global_severity: str,
        ai_diagnosis: str | None = None,
    ) -> SavedAnalysis | None:
        old = self.rows.get(id)
        if old is None:
            return None
        new = SavedAnalysis(
            id=old.id,
            name=old.name,
            equipment_identifier=old.equipment_identifier,
            incidents=incidents,
            global_severity=global_severity,
            ai_diagnosis=ai_diagnosis if ai_diagnosis is not None else old.ai_diagnosis,
            created_at=old.created_at,
        )
        self.rows[id] = new
        return new

    async def delete(self, id: UUID) -> bool:
        return self.rows.pop(id, None) is not None


class FakeTelemetryRepo:
    def __init__(self, events: list[TelemetryEvent] | None = None) -> None:
        self.events: list[TelemetryEvent] = list(events or [])

    async def add_events(self, events: list[TelemetryEvent]) -> None:
        self.events.extend(events)

    async def get_events_by_serial(self, serial: str) -> list[TelemetryEvent]:
        return [e for e in self.events if e.device_serial == serial]

    async def delete_by_analysis_id(self, analysis_id: UUID) -> int:
        before = len(self.events)
        self.events = [e for e in self.events if e.saved_analysis_id != analysis_id]
        return before - len(self.events)


class FakeCpmdRepo:
    def __init__(self) -> None:
        self.rows: dict[int, CpmdManual] = {}

    async def find_by_model_family(self, model_family: str) -> CpmdManual | None:
        for m in self.rows.values():
            if any(kw.upper() in model_family.upper() for kw in m.keywords):
                return m
        return None

    async def get_by_id(self, manual_id: int) -> CpmdManual | None:
        return self.rows.get(manual_id)

    async def create(self, *, keywords: list[str], label: str, filename: str) -> CpmdManual:
        manual = CpmdManual(
            id=len(self.rows) + 1, keywords=keywords, label=label, filename=filename,
            uploaded_at=NOW,
        )
        self.rows[manual.id] = manual
        return manual
