"""Puerto: wsAyC (Canal Directo) para incidentes CD por equipo.

Puerto local del módulo — no comparte tipos con el `WsAycGateway` de insumos
(ADR-018: la plomería del cliente SOAP se comparte vía
`shared/infrastructure/wsayc/`, el puerto y el parsing quedan por módulo).
"""

from __future__ import annotations

from typing import Protocol

from src.modules.analisis_log_hp.domain.entities.cds_incident import CdsReplacement


class CdsWsAycGateway(Protocol):
    async def get_machine_by_serial(self, serial: str) -> tuple[str, str] | None:
        """(machine_id, empresa_id), o None si el equipo no existe en CD."""
        ...

    async def get_machine_incidents(
        self, machine_id: str, empresa_id: str
    ) -> list[dict[str, str]]:
        """Incidentes crudos (dicts con Fecha/FechaCierre/Motivo/Tipo/Estado/id/
        NroIncidente) — sin filtrar ni ordenar, eso es del caso de uso."""
        ...

    async def get_counters(self, machine_id: str) -> list[dict[str, str]]:
        """Lecturas crudas de contador (FechaToma/Contador/TipoToma)."""
        ...

    async def get_incident_replacements(self, incident_id: str) -> list[CdsReplacement]: ...

    async def get_incident_jobs(self, incident_id: str) -> list[str]: ...
