"""Listado del análisis de equipos sin contador real: anota el operador
asignado a cada cliente (vía calendario local + cruce con Siges) y filtra,
busca y ordena en memoria sobre el snapshot cacheado del puerto — cada
interacción de la UI (orden, página, umbral) no dispara otra consulta cara
contra Siges."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.contadores.application.dtos.equipo_sin_real_anotado import (
    EquipoSinRealAnotado,
    OperadorAsignado,
)
from src.modules.contadores.application.dtos.list_equipos_sin_real_request import (
    ListEquiposSinRealRequest,
    SortBy,
)
from src.modules.contadores.application.use_cases.operador_por_empresa import (
    MapaOperadorPorEmpresa,
)
from src.modules.contadores.domain.ports.equipos_sin_real_port import EquiposSinRealPort

_SORT_KEYS: dict[SortBy, Callable[[EquipoSinRealAnotado], int | str | tuple[int, str]]] = {
    "meses": lambda a: a.equipo.meses_sin_real,
    "cliente": lambda a: a.equipo.cliente.casefold(),
    "sucursal": lambda a: a.equipo.sucursal.casefold(),
    "modelo": lambda a: a.equipo.modelo.casefold(),
    # Tupla para que los equipos sin operador queden siempre al final del
    # orden ascendente, no mezclados como "".
    "operador": lambda a: (0, a.operador.nombre.casefold()) if a.operador else (1, ""),
}


@dataclass(frozen=True)
class ListEquiposSinRealResult:
    equipos: list[EquipoSinRealAnotado]
    consultado_en: datetime


@dataclass(frozen=True, slots=True)
class ListEquiposSinRealDependencies:
    port: EquiposSinRealPort
    operador_mapa: MapaOperadorPorEmpresa | None
    """`None` degrada a listar sin columna de operador."""


class ListEquiposSinRealUseCase:
    def __init__(self, deps: ListEquiposSinRealDependencies) -> None:
        self._deps = deps

    async def execute(self, request: ListEquiposSinRealRequest) -> ListEquiposSinRealResult:
        snapshot = await self._deps.port.list_equipos(force_refresh=request.force_refresh)
        operadores = await self._mapa_operadores()
        anotados = [
            EquipoSinRealAnotado(equipo=e, operador=operadores.get(e.id_empresa_cliente))
            for e in snapshot.equipos
            if e.meses_sin_real >= request.min_meses
        ]
        if request.solo_operador_nombre:
            anotados = filtrar_por_operador(anotados, request.solo_operador_nombre)
        if request.search:
            anotados = _filtrar(anotados, request.search)
        anotados = _ordenar(anotados, request.sort_by, request.sort_dir == "desc")
        return ListEquiposSinRealResult(equipos=anotados, consultado_en=snapshot.consultado_en)

    async def _mapa_operadores(self) -> dict[int, OperadorAsignado]:
        if self._deps.operador_mapa is None:
            return {}
        return await self._deps.operador_mapa.build(hoy=datetime.now(UTC).date())


def filtrar_por_operador(
    anotados: list[EquipoSinRealAnotado], operador_nombre: str
) -> list[EquipoSinRealAnotado]:
    """Solo los equipos cuyo cliente está asignado a ese operador (cruce por
    nombre, insensible a mayúsculas). Los equipos sin operador resuelto quedan
    afuera: no se puede afirmar que sean de nadie."""
    nombre = operador_nombre.casefold()
    return [
        a for a in anotados if a.operador is not None and a.operador.nombre.casefold() == nombre
    ]


def _filtrar(anotados: list[EquipoSinRealAnotado], search: str) -> list[EquipoSinRealAnotado]:
    needle = search.casefold()
    return [
        a
        for a in anotados
        if needle in a.equipo.serie.casefold()
        or needle in a.equipo.cliente.casefold()
        or needle in a.equipo.sucursal.casefold()
        or needle in a.equipo.modelo.casefold()
        or (a.operador is not None and needle in a.operador.nombre.casefold())
    ]


def _ordenar(
    anotados: list[EquipoSinRealAnotado], sort_by: SortBy, descending: bool
) -> list[EquipoSinRealAnotado]:
    # Doble pasada estable: el desempate (cliente, sucursal, serie) queda
    # siempre ascendente aunque la clave principal se invierta.
    desempatados = sorted(
        anotados,
        key=lambda a: (a.equipo.cliente.casefold(), a.equipo.sucursal.casefold(), a.equipo.serie),
    )
    return sorted(desempatados, key=_SORT_KEYS[sort_by], reverse=descending)
