from datetime import date

from src.modules.contadores.domain.ports.historial_equipo_port import HistorialEquipoPort
from src.modules.contadores.domain.services.historial_equipo import (
    LecturaHistorial,
    enriquecer_historial,
)
from src.modules.contadores.domain.services.periodos_facturacion import restar_meses

_MESES_HISTORIAL = 24  # MODELO_DE_DATOS.md §3.6: línea de tiempo / drill-down


class GetHistorialEquipoUseCase:
    """Línea de tiempo de un equipo/clase (paridad con `DrillDownModal`
    legacy) — últimos 24 meses de lecturas, enriquecidas con Delta y
    clasificación de ubicación."""

    def __init__(self, port: HistorialEquipoPort) -> None:
        self._port = port

    async def execute(
        self, id_maquina: int, id_clase_contador: int, hoy: date | None = None
    ) -> list[LecturaHistorial]:
        desde = restar_meses(hoy or date.today(), _MESES_HISTORIAL)
        crudo = await self._port.fetch_historial(id_maquina, id_clase_contador, desde)
        return enriquecer_historial(crudo)
