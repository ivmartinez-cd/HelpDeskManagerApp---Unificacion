"""KPIs del análisis de equipos sin contador real, computados sobre el
universo completo del snapshot (>= 1 mes sin real), independientes del
filtro/orden que tenga aplicado la tabla."""

from dataclasses import dataclass
from datetime import datetime

from src.modules.contadores.domain.ports.equipos_sin_real_port import EquiposSinRealPort
from src.modules.contadores.domain.services.severidad_sin_real import severidad_por_meses


@dataclass(frozen=True)
class EquiposSinRealResumen:
    total: int
    criticos: int
    altos: int
    medios: int
    bajos: int
    nunca_real: int
    consultado_en: datetime


class GetEquiposSinRealResumenUseCase:
    def __init__(self, port: EquiposSinRealPort) -> None:
        self._port = port

    async def execute(self, *, force_refresh: bool = False) -> EquiposSinRealResumen:
        snapshot = await self._port.list_equipos(force_refresh=force_refresh)
        conteos = {"critico": 0, "alto": 0, "medio": 0, "bajo": 0}
        nunca_real = 0
        for equipo in snapshot.equipos:
            conteos[severidad_por_meses(equipo.meses_sin_real)] += 1
            if equipo.nunca_tuvo_real:
                nunca_real += 1
        return EquiposSinRealResumen(
            total=len(snapshot.equipos),
            criticos=conteos["critico"],
            altos=conteos["alto"],
            medios=conteos["medio"],
            bajos=conteos["bajo"],
            nunca_real=nunca_real,
            consultado_en=snapshot.consultado_en,
        )
