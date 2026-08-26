"""Caso de uso central de la pantalla: parque de una zona con vencimiento
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
from src.modules.preventivos.domain.entities.equipo_preventivo import EquipoPreventivo
from src.modules.preventivos.domain.entities.habilitacion_preventivo import (
    HabilitacionPreventivo,
)
from src.modules.preventivos.domain.errors import ZonaInvalidaError
from src.modules.preventivos.domain.repositories.habilitacion_repository import (
    HabilitacionRepository,
)
from src.modules.preventivos.domain.repositories.preventivos_query_gateway import (
    PreventivosQueryGateway,
)
from src.modules.preventivos.domain.services.vencimiento import (
    ORDEN_ESTADO_PRIORIDAD,
    calcular_vencimiento,
)
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
        zona = request.zona.strip()
        if zona_excluida(zona, self._deps.zonas_excluidas):
            raise ZonaInvalidaError(zona)
        snapshot = await self._deps.gateway.list_equipos_por_zona(
            zona, force_refresh=request.force_refresh
        )
        habilitaciones = await self._habilitaciones_vigentes(snapshot.equipos)
        hoy = datetime.now(_TZ_LOCAL).date()
        anotados = [
            _anotar(equipo, habilitaciones.get(equipo.id_maquina), hoy)
            for equipo in snapshot.equipos
        ]
        filtrados = [a for a in anotados if _pasa_filtros(a, request)]
        filtrados.sort(key=_orden_default)
        return ListEquiposResult(equipos=filtrados, consultado_en=snapshot.consultado_en)

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


def _pasa_filtros(
    anotado: EquipoPreventivoAnotado, request: ListEquiposPorZonaRequest
) -> bool:
    if request.estado is not None and anotado.estado != request.estado:
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


def _orden_default(anotado: EquipoPreventivoAnotado) -> tuple[int, int, str, str]:
    """Vencidos primero y el más atrasado arriba (la vista "se quedó sin
    servicios, qué le doy"); después los que nunca tuvieron preventivo, los
    por vencer más próximos, al día y sin frecuencia al final."""
    if anotado.estado == "vencido":
        secundario = -(anotado.dias_vencido or 0)
    elif anotado.proximo_vencimiento is not None:
        secundario = anotado.proximo_vencimiento.toordinal()
    else:
        secundario = 0
    cliente = anotado.equipo.cliente.lower()
    return (ORDEN_ESTADO_PRIORIDAD[anotado.estado], secundario, cliente, anotado.equipo.serie)
