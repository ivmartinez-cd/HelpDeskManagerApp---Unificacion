"""Puntos del mapa de clientes: reusa ListEquiposPorZonaUseCase (mismos
filtros, misma limpieza automática de habilitaciones cumplidas) y colapsa el
resultado de máquina a sucursal — el mapa es de sucursales, no de equipos."""

from dataclasses import dataclass

from src.modules.preventivos.application.dtos.equipo_preventivo_anotado import (
    EquipoPreventivoAnotado,
)
from src.modules.preventivos.application.dtos.list_equipos_request import (
    ListEquiposPorZonaRequest,
)
from src.modules.preventivos.application.dtos.punto_mapa_preventivo import (
    ListPuntosMapaResult,
    PuntoMapaPreventivo,
)
from src.modules.preventivos.application.use_cases.list_equipos_por_zona import (
    ListEquiposPorZonaUseCase,
)
from src.modules.preventivos.domain.services.coordenadas import coordenada_valida
from src.modules.preventivos.domain.services.vencimiento import ORDEN_ESTADO_PRIORIDAD


@dataclass(frozen=True, slots=True)
class ListPuntosMapaDependencies:
    equipos_use_case: ListEquiposPorZonaUseCase


class ListPuntosMapaUseCase:
    def __init__(self, deps: ListPuntosMapaDependencies) -> None:
        self._deps = deps

    async def execute(self, request: ListEquiposPorZonaRequest) -> ListPuntosMapaResult:
        resultado = await self._deps.equipos_use_case.execute(request)
        return ListPuntosMapaResult(
            puntos=_agrupar_por_sucursal(resultado.equipos),
            consultado_en=resultado.consultado_en,
        )


def _agrupar_por_sucursal(
    equipos: list[EquipoPreventivoAnotado],
) -> list[PuntoMapaPreventivo]:
    por_sucursal: dict[int, list[EquipoPreventivoAnotado]] = {}
    for anotado in equipos:
        por_sucursal.setdefault(anotado.equipo.id_sucursal, []).append(anotado)
    return [_punto(id_sucursal, grupo) for id_sucursal, grupo in por_sucursal.items()]


def _punto(id_sucursal: int, grupo: list[EquipoPreventivoAnotado]) -> PuntoMapaPreventivo:
    referencia = grupo[0].equipo
    peor = min(grupo, key=lambda a: ORDEN_ESTADO_PRIORIDAD[a.estado])
    vencidos = [
        a.dias_vencido for a in grupo if a.estado == "vencido" and a.dias_vencido is not None
    ]
    return PuntoMapaPreventivo(
        id_sucursal=id_sucursal,
        cliente=referencia.cliente,
        sucursal=referencia.sucursal,
        zona=referencia.zona,
        latitud=referencia.latitud,
        longitud=referencia.longitud,
        ubicado=coordenada_valida(referencia.latitud, referencia.longitud),
        cant_maquinas=len(grupo),
        cant_habilitadas=sum(1 for a in grupo if a.habilitacion is not None),
        peor_estado=peor.estado,
        dias_vencido_max=max(vencidos) if vencidos else None,
    )
