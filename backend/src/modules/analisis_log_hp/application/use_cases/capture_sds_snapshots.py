"""Caso de uso: capturar snapshots SDS automáticos de todos los equipos trackeados.

Job de fondo 2×/día (§2 caracterización). Para cada serial único en
saved_analyses: refresh de caché HP, extracción de logs, análisis y guardado
automático como 'Auto - {serial} - {fecha} (mañana|tarde)'.

Bug corregido (§12.bis): el legacy usaba inc.last_event_time sobre la entidad
Incident (campo que no existe) y nunca escribía telemetría desde los snapshots
automáticos. Acá se usa inc.end_time (campo correcto de la entidad).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from src.modules.analisis_log_hp.application.use_cases.saved_analyses import (
    _build_telemetry,
    incident_to_summary,
)
from src.modules.analisis_log_hp.domain.entities.incident import AnalysisResult
from src.modules.analisis_log_hp.domain.entities.saved_analysis import SavedAnalysis
from src.modules.analisis_log_hp.domain.repositories.error_code_repository import (
    ErrorCodeRepository,
)
from src.modules.analisis_log_hp.domain.repositories.hp_portal_gateway import (
    EventLogsResult,
    HpPortalGateway,
)
from src.modules.analisis_log_hp.domain.repositories.saved_analysis_repository import (
    SavedAnalysisRepository,
)
from src.modules.analisis_log_hp.domain.repositories.telemetry_repository import (
    TelemetryRepository,
)
from src.modules.analisis_log_hp.domain.services.analysis_service import analyze_events
from src.modules.analisis_log_hp.domain.services.log_enrichment import enrich_events
from src.modules.analisis_log_hp.domain.services.log_parser import (
    normalize_log_text,
    parse_log_text,
)

logger = logging.getLogger(__name__)


@dataclass
class SnapshotCaptureResult:
    serial: str
    skipped: bool
    snapshot_id: str | None = None
    incidents_count: int = 0
    error: str | None = None


class CaptureSdsSnapshots:
    def __init__(
        self,
        repo: SavedAnalysisRepository,
        telemetry: TelemetryRepository,
        error_code_repo: ErrorCodeRepository,
        portal: HpPortalGateway,
    ) -> None:
        self._repo = repo
        self._telemetry = telemetry
        self._error_code_repo = error_code_repo
        self._portal = portal

    async def execute_all(self) -> list[SnapshotCaptureResult]:
        page = await self._repo.list_page(1, 1000)
        serials = list(
            dict.fromkeys(
                s.equipment_identifier
                for s in page.items
                if s.equipment_identifier
            )
        )
        results: list[SnapshotCaptureResult] = []
        for serial in serials:
            results.append(await self._capture_one(serial))
        return results

    async def _capture_one(self, serial: str) -> SnapshotCaptureResult:
        try:
            analysis = await self._analyze_device(serial)
            if not analysis.incidents:
                return SnapshotCaptureResult(serial=serial, skipped=True)
            saved = await self._persist_snapshot(serial, analysis)
            return SnapshotCaptureResult(
                serial=serial,
                skipped=False,
                snapshot_id=str(saved.id),
                incidents_count=len(analysis.incidents),
            )
        except Exception as exc:
            logger.error("capture_sds: falló para serial=%s", serial, exc_info=exc)
            return SnapshotCaptureResult(serial=serial, skipped=False, error=str(exc))

    async def _fetch_logs(self, serial: str) -> EventLogsResult:
        """Resuelve el equipo en el portal, refresca su caché HP y baja los logs."""
        device = await self._portal.search_device(serial.strip().upper())
        device_id = device["id"]
        await self._portal.refresh_hp_cache(device_id)
        logs = await self._portal.fetch_event_logs(device_id, days=30)
        await self._update_catalog(serial, logs.help_urls)
        return logs

    async def _update_catalog(self, serial: str, help_urls: dict[str, dict[str, Any]]) -> None:
        """Falla del catálogo no frena la captura: se loguea y se sigue."""
        if not help_urls:
            return
        try:
            await self._error_code_repo.bulk_update_solution_urls(help_urls)
        except Exception as exc:
            logger.warning(
                "capture_sds: no se pudo actualizar catálogo serial=%s", serial, exc_info=exc
            )

    async def _analyze_device(self, serial: str) -> AnalysisResult:
        logs = await self._fetch_logs(serial)
        report = parse_log_text(normalize_log_text(logs.tsv))
        unique_codes = list(dict.fromkeys(e.code for e in report.events))
        catalog = await self._error_code_repo.get_by_codes(unique_codes)
        events = enrich_events(report.events, catalog)
        return analyze_events(events)

    async def _persist_snapshot(self, serial: str, analysis: AnalysisResult) -> SavedAnalysis:
        summaries = [incident_to_summary(i) for i in analysis.incidents]
        saved = await self._repo.create(
            name=_auto_snapshot_name(serial, datetime.now(UTC)),
            equipment_identifier=serial,
            incidents=summaries,
            global_severity=analysis.global_severity,
        )
        await self._telemetry.add_events(
            _build_telemetry(serial, saved.id, list(analysis.incidents))
        )
        return saved


def _auto_snapshot_name(serial: str, now: datetime) -> str:
    turno = "mañana" if now.hour < 14 else "tarde"
    return f"Auto - {serial} - {now.strftime('%Y-%m-%d')} ({turno})"
