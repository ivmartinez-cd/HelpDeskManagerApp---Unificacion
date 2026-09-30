"""Caso de uso central de la pantalla: parque de una o más zonas con vencimiento
calculado y habilitaciones locales cruzadas. Acá también vive la limpieza
automática de la decisión c del ADR del módulo: una habilitación activa cuyo
equipo ya tiene un preventivo cerrado en la fecha de habilitación o después
se desactiva sola (el pedido ya se cumplió)."""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from src.modules.preventivos.application.dtos.equipo_preventivo_anotado import (
    EquipoPreventivoAnotado,
    HabilitacionInfo,
    ListEquiposResult,
)
from src.modules.preventivos.application.dtos.list_equipos_request import (
    ListEquiposPorZonaRequest,
)
from src.modules.preventivos.application.use_cases.orden_equipos import ordenar_equipos
from src.modules.preventivos.domain.entities.equipo_preventivo import EquipoPreventivo
from src.modules.preventivos.domain.entities.habilitacion_preventivo import (
    HabilitacionPreventivo,
)
from src.modules.preventivos.domain.errors import ZonaInvalidaError, ZonaNoEncontradaError
from src.modules.preventivos.domain.repositories.habilitacion_repository import (
    HabilitacionRepository,
)
from src.modules.preventivos.domain.repositories.preventivos_query_gateway import (
    PreventivosQueryGateway,
)
from src.modules.preventivos.domain.services.vencimiento import calcular_vencimiento
from src.modules.preventivos.domain.services.zonas import zona_excluida

# Las fechas de Siges son hora local de Argentina; "hoy" del cálculo de
# vencimientos usa la misma zona (el contenedor corre en UTC).
_TZ_LOCAL = ZoneInfo("America/Argentina/Buenos_Aires")

DESHABILITADO_POR_SISTEMA = "sistema (preventivo registrado)"


@dataclass(frozen=True, slots=True)
class ListEquiposPorZonaDependencies:
    gateway: PreventivosQueryGateway
    habilitaciones: HabilitacionRepository
    zonas_excluidas: tuple[str, ...]


class ListEquiposPorZonaUseCase:
    def __init__(self, deps: ListEquiposPorZonaDependencies) -> None:
        self._deps = deps

    async def execute(self, request: ListEquiposPorZonaRequest) -> ListEquiposResult:
        zonas = list(dict.fromkeys(z.strip() for z in request.zonas))
        for zona in zonas:
            if zona_excluida(zona, self._deps.zonas_excluidas):
                raise ZonaInvalidaError(zona)
            await self._exigir_zona_conocida(zona)
        snapshots = [
            await self._deps.gateway.list_equipos_por_zona(
                zona, force_refresh=request.force_refresh
            )
            for zona in zonas
        ]
        equipos = tuple(e for s in snapshots for e in s.equipos)
        habilitaciones = await self._habilitaciones_vigentes(equipos)
        hoy = datetime.now(_TZ_LOCAL).date()
        anotados = [
            _anotar(equipo, habilitaciones.get(equipo.id_maquina), hoy) for equipo in equipos
        ]
        filtrados = [a for a in anotados if _pasa_filtros(a, request)]
        ordenados = ordenar_equipos(filtrados, request.orden, request.descendente)
        # El sello más viejo: es el que dice qué tan frescos son los datos.
        consultado_en = min(s.consultado_en for s in snapshots)
        return ListEquiposResult(equipos=ordenados, consultado_en=consultado_en)

    async def _exigir_zona_conocida(self, zona: str) -> None:
        """El catálogo de zonas está cacheado en el gateway (30 min); una zona
        con typo no paga la consulta completa del parque contra Siges."""
        conocidas = {z.zona.strip().upper() for z in await self._deps.gateway.list_zonas()}
        if zona.upper() not in conocidas:
            raise ZonaNoEncontradaError(zona)

    async def _habilitaciones_vigentes(
        self, equipos: tuple[EquipoPreventivo, ...]
    ) -> dict[int, HabilitacionPreventivo]:
        ultimo_preventivo = {e.id_maquina: e.fecha_ultimo_preventivo for e in equipos}
        activas = {
            h.siges_maquina_id: h
            for h in await self._deps.habilitaciones.list_activas_por_maquinas(
                list(ultimo_preventivo)
            )
        }
        for maquina_id, habilitacion in list(activas.items()):
            if _preventivo_cumplido(ultimo_preventivo.get(maquina_id), habilitacion):
                await self._deps.habilitaciones.desactivar(
                    maquina_id,
                    deshabilitado_por=DESHABILITADO_POR_SISTEMA,
                    deshabilitado_en=datetime.now(UTC),
                )
                del activas[maquina_id]
        return activas


def _preventivo_cumplido(
    fecha_ultimo_preventivo: date | None, habilitacion: HabilitacionPreventivo
) -> bool:
    # Comparación a nivel día: un preventivo cerrado el mismo día de la
    # habilitación cuenta como cumplido (la visita ya pasó).
    if fecha_ultimo_preventivo is None:
        return False
    return fecha_ultimo_preventivo >= habilitacion.habilitado_en.astimezone(_TZ_LOCAL).date()


def _anotar(
    equipo: EquipoPreventivo, habilitacion: HabilitacionPreventivo | None, hoy: date
) -> EquipoPreventivoAnotado:
    vencimiento = calcular_vencimiento(
        equipo.fecha_ultimo_preventivo,
        equipo.frecuencia_dias,
        hoy,
        fecha_instalacion=equipo.fecha_instalacion,
    )
    info = (
        HabilitacionInfo(
            habilitado_por=habilitacion.habilitado_por_nombre,
            habilitado_en=habilitacion.habilitado_en,
            nota=habilitacion.nota,
        )
        if habilitacion is not None
        else None
    )
    return EquipoPreventivoAnotado(
        equipo=equipo,
        estado=vencimiento.estado,
        proximo_vencimiento=vencimiento.proximo_vencimiento,
        dias_vencido=vencimiento.dias_vencido,
        fecha_tentativa=vencimiento.fecha_tentativa,
        habilitacion=info,
    )


def _pasa_filtros(anotado: EquipoPreventivoAnotado, request: ListEquiposPorZonaRequest) -> bool:
    if request.estados and anotado.estado not in request.estados:
        return False
    if request.habilitado is not None and (
        (anotado.habilitacion is not None) != request.habilitado
    ):
        return False
    if request.search and request.search.strip():
        q = request.search.strip().lower()
        equipo = anotado.equipo
        campos = (equipo.cliente, equipo.sucursal, equipo.serie, equipo.modelo)
        if not any(q in campo.lower() for campo in campos):
            return False
    return True
