from typing import Protocol

from src.modules.sla.domain.entities.incidente_sla import IncidenteSla
from src.modules.sla.domain.value_objects.periodo import Periodo


class SlaQueryGateway(Protocol):
    """Puerto de consulta en vivo a la base Siges (servidor MERCURIO). La
    implementación ejecuta la consulta legacy con Desde/Hasta derivados del
    período (primer/último día del mes) y devuelve las filas ya mapeadas."""

    async def find_incidentes(self, periodo: Periodo) -> list[IncidenteSla]: ...
