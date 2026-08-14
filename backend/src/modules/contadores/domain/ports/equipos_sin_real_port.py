from typing import Protocol

from src.modules.contadores.domain.entities.equipo_sin_real import EquiposSinRealSnapshot


class EquiposSinRealPort(Protocol):
    """Puerto del parque de equipos sin contador real reciente (>= 1 mes).

    Devuelve el universo completo: el filtrado por umbral de meses, búsqueda
    y orden son del caso de uso, para que un cambio de filtro/orden en la UI
    no dispare otra consulta cara contra Siges."""

    async def list_equipos(self, *, force_refresh: bool = False) -> EquiposSinRealSnapshot: ...
