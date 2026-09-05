"""Casos de uso CRUD de análisis guardados + comparación + salud del equipo.

Fan-out a telemetría al guardar/actualizar: delete anterior + insert nuevo
para evitar duplicación (§3.8, §5.10).
Bug corregido respecto al legacy (§12.bis): el snapshot automático usaba
inc.last_event_time sobre la entidad Incident (que no tiene ese campo).
Acá se usa end_time, que es el campo correcto.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from src.modules.analisis_log_hp.domain.entities.incident import Incident
from src.modules.analisis_log_hp.domain.entities.saved_analysis import (
    IncidentSummary,
    SavedAnalysis,
    TelemetryEvent,
)
from src.modules.analisis_log_hp.domain.errors import SavedAnalysisNameInvalidError
from src.modules.analisis_log_hp.domain.repositories.saved_analysis_repository import (
    SavedAnalysisRepository,
)
from src.modules.analisis_log_hp.domain.repositories.telemetry_repository import (
    TelemetryRepository,
)
from src.modules.analisis_log_hp.domain.services.compare_service import (
    compute_diff,
    diff_two_snapshots,
)
from src.modules.analisis_log_hp.domain.services.degradation_service import (
    DeviceHealth,
    evaluate_device_health,
)
from src.modules.analisis_log_hp.domain.services.log_enrichment import extract_serial_number
from src.shared.domain.errors import NotFoundError

logger = logging.getLogger(__name__)


def _make_aware(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def _nombre_valido(name: str) -> str:
    limpio = name.strip()
    if not limpio:
        raise SavedAnalysisNameInvalidError()
    return limpio


def incident_to_summary(inc: Incident) -> dict[str, Any]:
    end_iso = inc.end_time.isoformat()
    start_iso = inc.start_time.isoformat()
    return IncidentSummary(
        code=inc.code,
        classification=inc.classification,
        severity=inc.severity,
        occurrences=inc.occurrences,
        start_time=start_iso,
        end_time=end_iso,
        counter_range=list(inc.counter_range),
        sds_link=inc.sds_link,
        last_event_time=end_iso,
    ).to_dict()


def _build_telemetry(
    serial: str, analysis_id: UUID, incidents: list[Incident]
) -> list[TelemetryEvent]:
    return [
        TelemetryEvent(
            device_serial=serial,
            saved_analysis_id=analysis_id,
            code=inc.code,
            classification=inc.classification,
            severity=inc.severity,
            occurrences=inc.occurrences,
            counter=inc.counter_range[-1] if inc.counter_range else 0,
            event_time=inc.end_time,  # end_time, no last_event_time (bug legacy corregido)
        )
        for inc in incidents
    ]


class CreateSavedAnalysis:
    def __init__(self, repo: SavedAnalysisRepository, telemetry: TelemetryRepository) -> None:
        self._repo = repo
        self._telemetry = telemetry

    async def execute(
        self,
        name: str,
        equipment_identifier: str | None,
        incidents: list[Incident],
        global_severity: str,
        ai_diagnosis: str | None = None,
    ) -> SavedAnalysis:
        summaries = [incident_to_summary(i) for i in incidents]
        saved = await self._repo.create(
            _nombre_valido(name), equipment_identifier, summaries, global_severity, ai_diagnosis
        )
        if equipment_identifier:
            clean = extract_serial_number(equipment_identifier)
            if clean:
                await self._telemetry.add_events(_build_telemetry(clean, saved.id, incidents))
        return saved


class ListSavedAnalyses:
    def __init__(self, repo: SavedAnalysisRepository) -> None:
        self._repo = repo

    async def execute(self, page: int, size: int) -> tuple[list[SavedAnalysis], int]:
        return await self._repo.list_page(page, size)


class GetSavedAnalysis:
    def __init__(self, repo: SavedAnalysisRepository) -> None:
        self._repo = repo

    async def execute(self, id: UUID) -> SavedAnalysis:
        snap = await self._repo.get_by_id(id)
        if not snap:
            raise NotFoundError("Análisis guardado no encontrado")
        return snap


class UpdateSavedAnalysis:
    def __init__(self, repo: SavedAnalysisRepository, telemetry: TelemetryRepository) -> None:
        self._repo = repo
        self._telemetry = telemetry

    async def execute(
        self,
        id: UUID,
        name: str,
        equipment_identifier: str | None,
        incidents: list[Incident],
        global_severity: str,
        ai_diagnosis: str | None = None,
    ) -> SavedAnalysis:
        summaries = [incident_to_summary(i) for i in incidents]
        snap = await self._repo.update(
            id, _nombre_valido(name), summaries, global_severity, ai_diagnosis
        )
        if not snap:
            raise NotFoundError("Análisis guardado no encontrado")
        await self._telemetry.delete_by_analysis_id(id)
        if equipment_identifier:
            clean = extract_serial_number(equipment_identifier)
            if clean:
                await self._telemetry.add_events(_build_telemetry(clean, snap.id, incidents))
        return snap


class DeleteSavedAnalysis:
    def __init__(self, repo: SavedAnalysisRepository, telemetry: TelemetryRepository) -> None:
        self._repo = repo
        self._telemetry = telemetry

    async def execute(self, id: UUID) -> None:
        await self._telemetry.delete_by_analysis_id(id)
        deleted = await self._repo.delete(id)
        if not deleted:
            raise NotFoundError("Análisis guardado no encontrado")


@dataclass
class CompareResult:
    saved: SavedAnalysis
    diff: dict[str, Any]
    current_incidents: list[dict[str, Any]]
    current_global_severity: str
    current_events_count: int


class CompareAnalysisWithLog:
    """Compara un snapshot guardado contra un log nuevo (re-parseado)."""

    def __init__(self, repo: SavedAnalysisRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id: UUID,
        current_incidents: list[Incident],
        current_global_severity: str,
        current_events_count: int,
    ) -> CompareResult:
        snap = await self._repo.get_by_id(id)
        if not snap:
            raise NotFoundError("Análisis guardado no encontrado")

        now = datetime.now(UTC)
        saved_dt = _make_aware(snap.created_at)
        diferencia_dias = max(0, int((now - saved_dt).total_seconds() / 86400))

        current_by_code: dict[str, Any] = {inc.code: inc for inc in current_incidents}
        diff = compute_diff(snap.incidents, current_by_code)
        diff["diferencia_dias"] = diferencia_dias

        from src.modules.analisis_log_hp.domain.services.compare_service import calculate_trend

        diff["tendencia"] = calculate_trend(snap.incidents, current_by_code, diff)

        return CompareResult(
            saved=snap,
            diff=diff,
            current_incidents=[
                {
                    "code": inc.code,
                    "classification": inc.classification,
                    "severity": inc.severity,
                    "occurrences": inc.occurrences,
                    "start_time": inc.start_time.isoformat(),
                    "end_time": inc.end_time.isoformat(),
                    "counter_range": list(inc.counter_range),
                    "sds_link": inc.sds_link,
                }
                for inc in current_incidents
            ],
            current_global_severity=current_global_severity,
            current_events_count=current_events_count,
        )


class CompareSnapshots:
    """Compara dos snapshots guardados entre sí sin re-parsear logs."""

    def __init__(self, repo: SavedAnalysisRepository) -> None:
        self._repo = repo

    async def execute(self, id1: UUID, id2: UUID) -> dict[str, Any]:
        s1 = await self._repo.get_by_id(id1)
        s2 = await self._repo.get_by_id(id2)
        if not s1 or not s2:
            raise NotFoundError("Uno o ambos snapshots no encontrados")

        dt1 = _make_aware(s1.created_at)
        dt2 = _make_aware(s2.created_at)
        older, newer = (s1, s2) if dt1 <= dt2 else (s2, s1)
        older_dt = _make_aware(older.created_at)
        newer_dt = _make_aware(newer.created_at)
        diferencia_dias = max(0, int((newer_dt - older_dt).total_seconds() / 86400))

        diff = diff_two_snapshots(older.incidents, newer.incidents, diferencia_dias)
        return {"older": older, "newer": newer, "diff": diff}


@dataclass
class HealthResult:
    health: DeviceHealth
    events_count: int


class GetAnalysisHealth:
    def __init__(self, repo: SavedAnalysisRepository, telemetry: TelemetryRepository) -> None:
        self._repo = repo
        self._telemetry = telemetry

    async def execute(self, id: UUID) -> HealthResult:
        snap = await self._repo.get_by_id(id)
        if not snap:
            raise NotFoundError("Análisis guardado no encontrado")

        if not snap.equipment_identifier:
            return HealthResult(
                health=DeviceHealth(
                    "GREEN",
                    "Sin equipo asociado",
                    "El análisis no tiene identificador de equipo.",
                    "Sin acciones requeridas.",
                ),
                events_count=0,
            )
        clean = extract_serial_number(snap.equipment_identifier)
        if not clean:
            return HealthResult(
                health=DeviceHealth(
                    "GREEN",
                    "Sin serial",
                    "No se pudo extraer el serial.",
                    "Sin acciones requeridas.",
                ),
                events_count=0,
            )
        events = await self._telemetry.get_events_by_serial(clean)
        health = evaluate_device_health(events)  # type: ignore[arg-type]
        return HealthResult(health=health, events_count=len(events))
