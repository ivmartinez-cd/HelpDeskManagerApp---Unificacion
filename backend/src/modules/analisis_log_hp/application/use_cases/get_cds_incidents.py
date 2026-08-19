"""Caso de uso: incidentes CD (Canal Directo, vía wsAyC) para un serial.

Port del pipeline de `Printer-Logs-Analyzer/backend/application/services/
cds_service.py::get_cds_incidents_for_serial`: getMachineBySerial →
getMachineIncidents → últimos 12 meses, tope 15 → enriquecer c/u con contador
emparejado + repuestos + tareas (concurrencia acotada a 3, como el legacy).
Sin caché ni circuit breaker propios: la política de reintentos/timeouts ya
vive en el provider compartido (ADR-018).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from src.modules.analisis_log_hp.domain.entities.cds_incident import CdsIncident, CdsReplacement
from src.modules.analisis_log_hp.domain.repositories.wsayc_gateway import CdsWsAycGateway
from src.modules.analisis_log_hp.domain.services.cds_counter_matching import (
    find_counter_for_incident,
)

logger = logging.getLogger(__name__)

_FECHA_FMT = "%d/%m/%Y %H:%M:%S"
_MAX_INCIDENTS = 15
_MAX_CONCURRENT = 3


class GetCdsIncidents:
    def __init__(self, gateway: CdsWsAycGateway) -> None:
        self._gateway = gateway

    async def execute(self, serial: str) -> list[CdsIncident]:
        machine = await self._gateway.get_machine_by_serial(serial.strip().upper())
        if not machine:
            return []
        machine_id, empresa_id = machine
        raw = await self._gateway.get_machine_incidents(machine_id, empresa_id)
        recent = _recent_within_12_months(raw)[:_MAX_INCIDENTS]
        counters = await self._gateway.get_counters(machine_id)

        sem = asyncio.Semaphore(_MAX_CONCURRENT)
        results = await asyncio.gather(*[self._enrich(inc, counters, sem) for inc in recent])
        return sorted(results, key=_sort_key, reverse=True)

    async def _enrich(
        self,
        inc: dict[str, str],
        counters: list[dict[str, str]],
        sem: asyncio.Semaphore,
    ) -> CdsIncident:
        async with sem:
            incident_id = inc.get("id") or ""
            contador = find_counter_for_incident(
                counters, inc.get("Fecha", ""), inc.get("FechaCierre")
            )
            repuestos, tareas = await self._fetch_details(incident_id)
            return _to_entity(inc, incident_id, contador, repuestos, tareas)

    async def _fetch_details(
        self, incident_id: str
    ) -> tuple[list[CdsReplacement], list[str]]:
        if not incident_id:
            return [], []
        try:
            repuestos = await self._gateway.get_incident_replacements(incident_id)
            tareas = await self._gateway.get_incident_jobs(incident_id)
            return repuestos, tareas
        except Exception as exc:
            logger.warning(
                "get_cds_incidents: detalle del incidente %s falló",
                incident_id,
                exc_info=exc,
            )
            return [], []


def _recent_within_12_months(raw: list[dict[str, str]]) -> list[dict[str, str]]:
    cutoff = datetime.now() - timedelta(days=365)
    out = []
    for inc in raw:
        fecha_str = inc.get("Fecha")
        if not fecha_str:
            continue
        try:
            if datetime.strptime(fecha_str, _FECHA_FMT) >= cutoff:
                out.append(inc)
        except ValueError:
            continue
    return out


def _sort_key(inc: CdsIncident) -> datetime:
    try:
        return datetime.strptime(inc.fecha, _FECHA_FMT)
    except ValueError:
        return datetime.min


def _to_entity(
    inc: dict[str, str],
    incident_id: str,
    contador: str | None,
    repuestos: list[CdsReplacement],
    tareas: list[str],
) -> CdsIncident:
    return CdsIncident(
        id=incident_id,
        numero_incidente=inc.get("NroIncidente", ""),
        fecha=inc.get("Fecha", ""),
        fecha_cierre=inc.get("FechaCierre"),
        tipo=inc.get("Tipo", "Desconocido"),
        estado=inc.get("Estado", "Desconocido"),
        motivo=inc.get("Motivo", "Sin motivo"),
        contador=contador,
        repuestos=repuestos,
        tareas_realizadas=tareas,
    )
