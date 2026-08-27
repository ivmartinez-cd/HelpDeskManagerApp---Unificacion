from datetime import date
from typing import Protocol

from src.modules.sla.domain.entities.incidente_derivado import IncidenteDerivado


class DerivadosQueryGateway(Protocol):
    """Puerto de consulta en vivo a Siges para incidentes en estado
    'Derivado' (ID_Estado_Incidente=200, tipos 101/108) dentro de un rango de
    fechas. Sin filtro de PST del interior acá — lo aplica el caso de uso
    (mismo criterio que PendientesQueryGateway)."""

    async def find_incidentes_derivados(
        self, desde: date, hasta: date
    ) -> list[IncidenteDerivado]: ...
