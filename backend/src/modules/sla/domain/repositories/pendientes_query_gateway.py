from typing import Protocol

from src.modules.sla.domain.entities.incidente_sin_cerrar import IncidenteSinCerrar


class PendientesQueryGateway(Protocol):
    """Puerto de consulta en vivo a Siges para incidentes en estado
    'Finalizado' (ID_Estado_Incidente=500, tipos 101/108). Solo PST del
    interior — los técnicos CD no aparecen en la tabla local de prestadores y
    quedan excluidos por el filtro de visibilidad en presentación."""

    async def find_incidentes_sin_cerrar(
        self, meses_corte: int
    ) -> list[IncidenteSinCerrar]: ...
