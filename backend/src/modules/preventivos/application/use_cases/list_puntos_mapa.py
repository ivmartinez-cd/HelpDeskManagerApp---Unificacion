"""Puntos del mapa de clientes: reusa ListEquiposPorZonaUseCase (mismos
filtros, misma limpieza automática de habilitaciones cumplidas) y colapsa el
resultado de máquina a sucursal — el mapa es de sucursales, no de equipos.
Una coordenada resuelta por geocodificar_sucursales.py siempre pisa la de
Siges, incluso si esta última pasa la validación de bbox: puede ser un pin
compartido con otra sucursal (ver domain/services/pines_sospechosos.py), válido
mecánicamente pero no confiable."""

from dataclasses import dataclass, replace
from datetime import date

from src.modules.preventivos.application.dtos.equipo_preventivo_anotado import (
    EquipoPreventivoAnotado,
)
from src.modules.preventivos.application.dtos.list_equipos_request import (
    ListEquiposPorZonaRequest,
)
from src.modules.preventivos.application.dtos.punto_mapa_preventivo import (
    ConteoEstado,
    ListPuntosMapaResult,
    PuntoMapaPreventivo,
)
from src.modules.preventivos.application.use_cases.list_equipos_por_zona import (
    ListEquiposPorZonaUseCase,
)
from src.modules.preventivos.domain.entities.sucursal_coordenadas import SucursalCoordenadas
from src.modules.preventivos.domain.repositories.sucursal_coordenadas_repository import (
    SucursalCoordenadasRepository,
)
from src.modules.preventivos.domain.services.coordenadas import coordenada_valida
from src.modules.preventivos.domain.services.vencimiento import ORDEN_ESTADO_PRIORIDAD
from src.modules.preventivos.domain.value_objects.vencimiento_preventivo import (
    EstadoPreventivo,
)


@dataclass(frozen=True, slots=True)
class ListPuntosMapaDependencies:
    equipos_use_case: ListEquiposPorZonaUseCase
    sucursal_coordenadas: SucursalCoordenadasRepository


class ListPuntosMapaUseCase:
    def __init__(self, deps: ListPuntosMapaDependencies) -> None:
        self._deps = deps

    async def execute(self, request: ListEquiposPorZonaRequest) -> ListPuntosMapaResult:
        resultado = await self._deps.equipos_use_case.execute(request)
        puntos = _agrupar_por_sucursal(resultado.equipos)
        overrides = await self._overrides(puntos)
        return ListPuntosMapaResult(
            puntos=[_con_override(p, overrides.get(p.id_sucursal)) for p in puntos],
            consultado_en=resultado.consultado_en,
        )

    async def _overrides(
        self, puntos: list[PuntoMapaPreventivo]
    ) -> dict[int, SucursalCoordenadas]:
        ids = [p.id_sucursal for p in puntos]
        if not ids:
            return {}
        return await self._deps.sucursal_coordenadas.list_by_siges_sucursal_ids(ids)


def _con_override(
    punto: PuntoMapaPreventivo, override: SucursalCoordenadas | None
) -> PuntoMapaPreventivo:
    if override is None:
        return punto
    return replace(punto, latitud=override.latitud, longitud=override.longitud, ubicado=True)


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
    return PuntoMapaPreventivo(
        id_sucursal=id_sucursal,
        cliente=referencia.cliente,
        sucursal=referencia.sucursal,
        zona=referencia.zona,
        domicilio=referencia.domicilio,
        latitud=referencia.latitud,
        longitud=referencia.longitud,
        ubicado=coordenada_valida(referencia.latitud, referencia.longitud),
        cant_maquinas=len(grupo),
        cant_habilitadas=sum(1 for a in grupo if a.habilitacion is not None),
        peor_estado=peor.estado,
        fecha_vencido_min=_fecha_vencido_min(grupo),
        fecha_tentativa_min=_fecha_tentativa_min(grupo),
        distribucion=_distribucion(grupo),
    )


def _fecha_vencido_min(grupo: list[EquipoPreventivoAnotado]) -> date | None:
    # El más atrasado (mayor dias_vencido) es el de proximo_vencimiento más
    # antiguo — misma máquina, otra forma de mirarlo. El popup del mapa
    # prefiere la fecha real ("preventivo sugerido") a un conteo de días.
    vencidos = [
        a.proximo_vencimiento
        for a in grupo
        if a.estado == "vencido" and a.proximo_vencimiento is not None
    ]
    return min(vencidos) if vencidos else None


def _fecha_tentativa_min(grupo: list[EquipoPreventivoAnotado]) -> date | None:
    tentativas = [
        a.fecha_tentativa
        for a in grupo
        if a.estado == "sin_preventivo" and a.fecha_tentativa is not None
    ]
    return min(tentativas) if tentativas else None


def _distribucion(grupo: list[EquipoPreventivoAnotado]) -> tuple[ConteoEstado, ...]:
    conteos: dict[EstadoPreventivo, int] = {}
    for anotado in grupo:
        conteos[anotado.estado] = conteos.get(anotado.estado, 0) + 1
    # Recorre `ORDEN_ESTADO_PRIORIDAD` (no `conteos`) para que el desglose
    # salga siempre vencidos-primero, igual que el resto del módulo.
    return tuple(
        ConteoEstado(estado=estado, cantidad=conteos[estado])
        for estado in ORDEN_ESTADO_PRIORIDAD
        if estado in conteos
    )
