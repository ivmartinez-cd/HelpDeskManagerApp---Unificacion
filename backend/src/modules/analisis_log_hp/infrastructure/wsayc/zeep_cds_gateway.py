"""Adapter zeep del puerto CdsWsAycGateway (SOAP wsAyC de Canal Directo).

zeep es sincrónico (requests) — cada llamada corre en un thread
(asyncio.to_thread) para no bloquear el event loop. El cliente sale del
provider compartido (ADR-018): WSDL parseado una vez por proceso, Session
propia por llamada, transporte sin reintentos, timeout explícito — ver
`shared/infrastructure/wsayc/client_provider.py`.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.modules.analisis_log_hp.domain.entities.cds_incident import CdsReplacement
from src.modules.analisis_log_hp.infrastructure.wsayc import cds_parsing as parsing
from src.shared.infrastructure.wsayc.client_provider import (
    WsAycClientProvider,
    get_wsayc_client_provider,
)

logger = logging.getLogger(__name__)


class ZeepCdsGateway:
    def __init__(self, provider: WsAycClientProvider | None = None) -> None:
        self._provider = provider or get_wsayc_client_provider()

    def _service(self) -> Any:
        return self._provider.service()

    async def get_machine_by_serial(self, serial: str) -> tuple[str, str] | None:
        raw = await asyncio.to_thread(
            lambda: self._service().getMachineBySerial(SerialNumber=serial)
        )
        return parsing.parse_machine(raw)

    async def get_machine_incidents(
        self, machine_id: str, empresa_id: str
    ) -> list[dict[str, str]]:
        try:
            raw = await asyncio.to_thread(
                lambda: self._service().getMachineIncidents(
                    IdMaquina=machine_id, IdEmpresa=empresa_id or "",
                    IdSucursal="", IdSector="", top="50", estado="", tipo="Todos",
                )
            )
            return parsing.parse_incidents(raw)
        except Exception as exc:
            logger.warning(
                "SOAP getMachineIncidents(maquina=%s) falló", machine_id, exc_info=exc
            )
            return []

    async def get_counters(self, machine_id: str) -> list[dict[str, str]]:
        try:
            raw = await asyncio.to_thread(
                lambda: self._service().getCounters(IdMaquina=machine_id)
            )
            return parsing.parse_counters(raw)
        except Exception as exc:
            logger.warning("SOAP getCounters(maquina=%s) falló", machine_id, exc_info=exc)
            return []

    async def get_incident_replacements(self, incident_id: str) -> list[CdsReplacement]:
        try:
            raw = await asyncio.to_thread(
                lambda: self._service().getIncidentReplacements(id=incident_id)
            )
            return parsing.parse_replacements(raw)
        except Exception as exc:
            logger.warning(
                "SOAP getIncidentReplacements(%s) falló", incident_id, exc_info=exc
            )
            return []

    async def get_incident_jobs(self, incident_id: str) -> list[str]:
        try:
            raw = await asyncio.to_thread(
                lambda: self._service().getIncidentJobs(id=incident_id)
            )
            return parsing.parse_jobs(raw)
        except Exception as exc:
            logger.warning("SOAP getIncidentJobs(%s) falló", incident_id, exc_info=exc)
            return []
