from typing import Protocol

from src.modules.sla.domain.entities.incidente_mesa_ayuda import IncidenteMesaAyuda


class MesaAyudaQueryGateway(Protocol):
    async def find_incidentes_mesa_ayuda(self, id_tecnico: int) -> list[IncidenteMesaAyuda]: ...
