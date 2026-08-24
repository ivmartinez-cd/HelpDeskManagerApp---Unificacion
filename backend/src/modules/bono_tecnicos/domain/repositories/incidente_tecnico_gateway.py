from typing import Protocol

from src.modules.bono_tecnicos.domain.entities.incidente_bono import IncidenteBono
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


class IncidenteTecnicoGateway(Protocol):
    """Puerto de consulta en vivo a Siges (servidor MERCURIO) para el
    detalle de incidentes de un técnico puntual — mismo filtro base que
    `ConteoTecnicoGateway`, sin agrupar, para la pantalla de detalle."""

    async def find_incidentes(self, periodo: Periodo, id_tecnico: int) -> list[IncidenteBono]: ...
