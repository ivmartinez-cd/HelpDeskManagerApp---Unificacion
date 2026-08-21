"""KPIs del análisis de equipos sin contador real, computados sobre el
universo completo del snapshot (>= 1 mes sin real), independientes del
filtro/orden que tenga aplicado la tabla. Con `solo_operador_nombre` el
universo se acota a los clientes asignados a ese operador (mismo criterio
que el listado: lo que ve un operador sin `contadores.manage`)."""

from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.contadores.application.dtos.equipo_sin_real_anotado import OperadorAsignado
from src.modules.contadores.application.use_cases.operador_por_empresa import (
    MapaOperadorPorEmpresa,
)
from src.modules.contadores.domain.entities.equipo_sin_real import EquipoSinReal
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
    def __init__(
        self, port: EquiposSinRealPort, operador_mapa: MapaOperadorPorEmpresa | None = None
    ) -> None:
        self._port = port
        self._operador_mapa = operador_mapa

    async def execute(
        self, *, force_refresh: bool = False, solo_operador_nombre: str | None = None
    ) -> EquiposSinRealResumen:
        snapshot = await self._port.list_equipos(force_refresh=force_refresh)
        equipos = snapshot.equipos
        if solo_operador_nombre:
            equipos = await self._solo_de(equipos, solo_operador_nombre)
        conteos = {"critico": 0, "alto": 0, "medio": 0, "bajo": 0}
        nunca_real = 0
        for equipo in equipos:
            conteos[severidad_por_meses(equipo.meses_sin_real)] += 1
            if equipo.nunca_tuvo_real:
                nunca_real += 1
        return EquiposSinRealResumen(
            total=len(equipos),
            criticos=conteos["critico"],
            altos=conteos["alto"],
            medios=conteos["medio"],
            bajos=conteos["bajo"],
            nunca_real=nunca_real,
            consultado_en=snapshot.consultado_en,
        )

    async def _solo_de(self, equipos: list[EquipoSinReal], nombre: str) -> list[EquipoSinReal]:
        mapa: dict[int, OperadorAsignado] = (
            {}
            if self._operador_mapa is None
            else await self._operador_mapa.build(hoy=datetime.now(UTC).date())
        )
        objetivo = nombre.casefold()
        return [
            e
            for e in equipos
            if (op := mapa.get(e.id_empresa_cliente)) is not None
            and op.nombre.casefold() == objetivo
        ]
