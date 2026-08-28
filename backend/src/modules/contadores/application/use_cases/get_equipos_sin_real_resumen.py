"""KPIs del análisis de equipos sin contador real. Las tarjetas de severidad
(críticos/altos/medios/bajos/nunca real/no localizados) se computan sobre el
universo completo del snapshot (>= 1 mes sin real), independientes del
filtro/orden que tenga aplicado la tabla — sirven de referencia estable. El
desglose por operador, en cambio, sí sigue `min_meses`/`solo_activos` (mismos
filtros que la tabla de abajo): decisión del usuario 2026-08-28, para que lo
que se ve en el gráfico coincida con lo que se está mirando en la tabla. Con
`solo_operador_nombre` el universo se acota a los clientes asignados a ese
operador (mismo criterio que el listado: lo que ve un operador sin
`contadores.manage`)."""

from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.contadores.application.dtos.equipo_sin_real_anotado import OperadorAsignado
from src.modules.contadores.application.use_cases.operador_por_empresa import (
    MapaOperadorPorEmpresa,
)
from src.modules.contadores.domain.entities.equipo_sin_real import EquipoSinReal
from src.modules.contadores.domain.ports.equipos_sin_real_port import EquiposSinRealPort
from src.modules.contadores.domain.services.estado_maquina_sin_real import (
    ACTIVA_EN_CLIENTE,
    NO_LOCALIZADO,
)
from src.modules.contadores.domain.services.severidad_sin_real import severidad_por_meses

_SIN_OPERADOR = "Sin operador asignado"


@dataclass(frozen=True)
class OperadorSinReal:
    nombre: str
    color: str | None
    equipos: int
    # Parque total elegible de ese operador (mismos estados que el
    # numerador, sin filtro de fecha) — `None` para "Sin operador asignado",
    # que no tiene una cartera propia sobre la que calcular una tasa.
    parque_total: int | None


@dataclass(frozen=True)
class EquiposSinRealResumen:
    total: int
    criticos: int
    altos: int
    medios: int
    bajos: int
    nunca_real: int
    no_localizados: int
    operadores: list[OperadorSinReal]
    consultado_en: datetime


class GetEquiposSinRealResumenUseCase:
    def __init__(
        self, port: EquiposSinRealPort, operador_mapa: MapaOperadorPorEmpresa | None = None
    ) -> None:
        self._port = port
        self._operador_mapa = operador_mapa

    async def execute(
        self,
        *,
        force_refresh: bool = False,
        solo_operador_nombre: str | None = None,
        min_meses: int = 1,
        solo_activos: bool = False,
    ) -> EquiposSinRealResumen:
        snapshot = await self._port.list_equipos(force_refresh=force_refresh)
        equipos = snapshot.equipos
        mapa = await self._mapa_operadores()
        parque = await self._port.parque_elegible_por_empresa(force_refresh=force_refresh)
        if solo_operador_nombre:
            equipos = self._solo_de(equipos, mapa, solo_operador_nombre)
        criticos, altos, medios, bajos, nunca_real = self._contar_severidades(equipos)
        equipos_operador = self._filtrar_como_tabla(equipos, min_meses, solo_activos)
        return EquiposSinRealResumen(
            total=len(equipos),
            criticos=criticos,
            altos=altos,
            medios=medios,
            bajos=bajos,
            nunca_real=nunca_real,
            no_localizados=self._contar_no_localizados(equipos),
            operadores=self._agrupar_por_operador(equipos_operador, mapa, parque),
            consultado_en=snapshot.consultado_en,
        )

    async def _mapa_operadores(self) -> dict[int, OperadorAsignado]:
        if self._operador_mapa is None:
            return {}
        return await self._operador_mapa.build(hoy=datetime.now(UTC).date())

    @staticmethod
    def _contar_severidades(equipos: list[EquipoSinReal]) -> tuple[int, int, int, int, int]:
        conteos = {"critico": 0, "alto": 0, "medio": 0, "bajo": 0}
        nunca_real = 0
        for equipo in equipos:
            conteos[severidad_por_meses(equipo.meses_sin_real)] += 1
            if equipo.nunca_tuvo_real:
                nunca_real += 1
        return conteos["critico"], conteos["alto"], conteos["medio"], conteos["bajo"], nunca_real

    @staticmethod
    def _contar_no_localizados(equipos: list[EquipoSinReal]) -> int:
        return sum(1 for e in equipos if e.estado_maquina == NO_LOCALIZADO)

    @staticmethod
    def _filtrar_como_tabla(
        equipos: list[EquipoSinReal], min_meses: int, solo_activos: bool
    ) -> list[EquipoSinReal]:
        """Mismos dos filtros que ve la tabla (`list_equipos_sin_real`), para
        que el desglose por operador coincida con lo que se está mirando."""
        return [
            e
            for e in equipos
            if e.meses_sin_real >= min_meses
            and (not solo_activos or e.estado_maquina == ACTIVA_EN_CLIENTE)
        ]

    @staticmethod
    def _solo_de(
        equipos: list[EquipoSinReal], mapa: dict[int, OperadorAsignado], nombre: str
    ) -> list[EquipoSinReal]:
        objetivo = nombre.casefold()
        return [
            e
            for e in equipos
            if (op := mapa.get(e.id_empresa_cliente)) is not None
            and op.nombre.casefold() == objetivo
        ]

    @staticmethod
    def _agrupar_por_operador(
        equipos: list[EquipoSinReal],
        mapa: dict[int, OperadorAsignado],
        parque: dict[int, int],
    ) -> list[OperadorSinReal]:
        conteos, colores = _conteos_y_colores(equipos, mapa)
        parque_por_operador = _parque_por_operador(mapa, parque)
        return [
            OperadorSinReal(
                nombre=nombre,
                color=colores[nombre],
                equipos=conteos[nombre],
                parque_total=parque_por_operador.get(nombre) if nombre != _SIN_OPERADOR else None,
            )
            for nombre in sorted(conteos, key=lambda n: (-conteos[n], n))
        ]


def _conteos_y_colores(
    equipos: list[EquipoSinReal], mapa: dict[int, OperadorAsignado]
) -> tuple[dict[str, int], dict[str, str | None]]:
    conteos: dict[str, int] = {}
    colores: dict[str, str | None] = {}
    for equipo in equipos:
        op = mapa.get(equipo.id_empresa_cliente)
        nombre = op.nombre if op else _SIN_OPERADOR
        conteos[nombre] = conteos.get(nombre, 0) + 1
        colores.setdefault(nombre, op.color if op else None)
    return conteos, colores


def _parque_por_operador(
    mapa: dict[int, OperadorAsignado], parque: dict[int, int]
) -> dict[str, int]:
    """Parque total por operador, sumado una sola vez por empresa (no por
    equipo — un operador con varios equipos sin real en la misma empresa no
    puede inflar su propio denominador)."""
    total: dict[str, int] = {}
    for id_empresa, op in mapa.items():
        total[op.nombre] = total.get(op.nombre, 0) + parque.get(id_empresa, 0)
    return total
