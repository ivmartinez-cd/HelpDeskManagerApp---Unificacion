"""ReconciliarLiquidacion — colaborador de SincronizarLiquidaciones.

Actualiza in-place los incidentes de una liquidación que ya existe localmente
cuando AyC reporta cambios (costos, km, y los campos descriptivos que consume el
motor de reglas), pisa su `estado` con el que reporta AyC y trae su ítem extra y
número de factura (`Extra`/`DetalleExtra`/`FacturaLocal`/`FacturaNro` de
`getLiquidationById`, P4) cuando AyC tiene alguno cargado — la contraparte de
`_procesar` en `sincronizar_liquidaciones.py`, que solo crea liquidaciones
nuevas.

Una liquidación en estado terminal (aprobada/cerrada) nunca reconcilia
incidentes ni alertas — eso queda congelado para siempre (decisión consciente:
no reabrir liquidaciones ya cerradas). El extra/factura es la excepción: en la
práctica AyC suele cargar la factura en el mismo momento en que aprueba la
liquidación, así que si también se lo bloqueara acá ese dato nunca llegaría a
sincronizarse (hallazgo 2026-08-21, liquidaciones 3905-7/3929-7
aprobadas/cerradas sin factura local pese a tenerla en AyC) — una liquidación
terminal sigue trayendo extra/factura vía `_solo_estado_extra_y_factura`, sin
tocar incidentes/alertas.

El `estado` sí tiene una única transición permitida en terminal:
aprobada→cerrada, cuando AyC ya la reporta cerrada (hallazgo 2026-08-25:
liquidaciones que AyC cerraba después de aprobarlas quedaban mostrando
"Aprobada" para siempre porque el guard las trataba como igualmente
terminales). Nunca reabre desde cerrada, y no acepta ningún otro estado que
AyC reporte para una liquidación aprobada (una regresión aparente —AyC
reportando un estado anterior— se ignora, no se aplica).

Orden fijo dentro de una liquidación: bajas → cambios → altas → recálculo de
totales → reanálisis → recálculo de período → pisar estado → traer extra/factura.
El motor de reglas corre sobre el set de incidentes ya reconciliado, antes de
pisar estado y traer el extra/factura (ninguno de los dos afecta al motor) — si
reanalizara antes de las bajas, regeneraría alertas para incidentes que está por
borrar. El estado se pisa con el que reportaba AyC *antes* de reconciliar los
incidentes (`cd_liq`, no se vuelve a consultar) — evaluar el guard de estado
terminal contra el estado local previo, no el nuevo, así una liquidación recién
marcada `aprobada` en AyC también recibe esta última reconciliación de incidentes.

El recálculo de período corre siempre (haya o no diff de incidentes) usando el
set de incidentes ya reconciliado — a diferencia de totales/reanálisis, que solo
tienen sentido si algo cambió. Sin esto, una liquidación creada con el período
fijado por el fallback de `extraer_periodo` (sus incidentes no tenían todavía
`fecha_cierre`) quedaba con el período viejo para siempre en cuanto los
incidentes cerraban sin generar ningún otro diff (caso real: liquidación 3935-8,
Tres Arroyos, agosto 2026 — incidentes y totales ya coincidían con AyC, pero el
período seguía en 2026-03 con incidentes cerrados en abril/junio).

Nunca borra y recrea un incidente que sigue existiendo remotamente (`cambios`
hace UPDATE in-place, preserva `incidente_id`) — ver
`domain/services/reconciliar_incidentes.py` para el porqué (`alertas.incidente_id`
es `ON DELETE CASCADE`; recrear el incidente se llevaría el triage de la TL).

`total_importe` incluye el ítem extra (ver `recalcular_total_extra` — hallazgo
2026-08-25, liquidación 3907-5). Como el recálculo por diff de incidentes
(`_actualizar_totales`) puede correr en la misma pasada y antes que el ajuste
por extra (`_actualizar_extra`), `execute()` arma una copia corregida de
`liquidacion` con el total ya actualizado por incidentes antes de pasarla a
`_actualizar_extra_y_factura` — si no, el ajuste por extra partiría de un
`total_importe` desactualizado (previo al diff) y pisaría el recálculo de
incidentes.
"""

from dataclasses import dataclass, replace
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._reconciliar_extra_y_factura import (
    actualizar_extra_y_factura,
)
from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
)
from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.liquidacion import (
    ESTADO_APROBADA,
    ESTADO_CERRADA,
    Liquidacion,
)
from src.modules.liquidaciones.domain.repositories.cd_liquidaciones_gateway import (
    CdLiquidacionesGateway,
)
from src.modules.liquidaciones.domain.repositories.incidente_repository import (
    IncidenteRepository,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.modules.liquidaciones.domain.services.estados_ayc import estado_local_desde_ayc
from src.modules.liquidaciones.domain.services.importacion.metadata import periodo_mas_frecuente
from src.modules.liquidaciones.domain.services.recalcular_total_extra import (
    total_importe_con_incidentes_y_extra,
)
from src.modules.liquidaciones.domain.services.reconciliar_incidentes import (
    DiffIncidentes,
    reconciliar_incidentes,
)
from src.modules.liquidaciones.domain.services.tipo_abono import tipo_segun_incidentes
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import CdLiquidacion
from src.modules.liquidaciones.domain.value_objects.incidente_importado import IncidenteImportado

_ESTADOS_TERMINALES = frozenset({ESTADO_APROBADA, ESTADO_CERRADA})
# Por encima de este umbral, un mismatch de matching (no un cambio real en AyC)
# es más probable que la explicación — abortar es más seguro que borrar en masa.
_UMBRAL_BAJAS_MASIVAS = 0.5


@dataclass(frozen=True)
class ReconciliarLiquidacionPorts:
    incidentes: IncidenteRepository
    liquidaciones: LiquidacionRepository
    reanalizar: ReanalizarLiquidacion
    cd_gateway: CdLiquidacionesGateway


@dataclass(frozen=True)
class ReconciliarLiquidacionResultado:
    reconciliada: bool
    altas: int = 0
    cambios: int = 0
    bajas: int = 0
    estado_actualizado: bool = False
    periodo_actualizado: bool = False
    extra_actualizado: bool = False
    factura_actualizada: bool = False


class ReconciliarLiquidacion:
    def __init__(self, ports: ReconciliarLiquidacionPorts) -> None:
        self._ports = ports

    async def execute(
        self, liquidacion: Liquidacion, cd_liq: CdLiquidacion, remotos: list[IncidenteImportado]
    ) -> ReconciliarLiquidacionResultado:
        if liquidacion.estado in _ESTADOS_TERMINALES:
            return await self._solo_estado_extra_y_factura(liquidacion, cd_liq)
        return await self._reconciliar_no_terminal(liquidacion, cd_liq, remotos)

    async def _reconciliar_no_terminal(
        self, liquidacion: Liquidacion, cd_liq: CdLiquidacion, remotos: list[IncidenteImportado]
    ) -> ReconciliarLiquidacionResultado:
        if len(remotos) != cd_liq.cant_incidentes:
            return ReconciliarLiquidacionResultado(reconciliada=False)

        locales = await self._ports.incidentes.list_by_liquidacion(liquidacion.id)
        diff = reconciliar_incidentes(locales, remotos)
        if locales and len(diff.bajas) / len(locales) > _UMBRAL_BAJAS_MASIVAS:
            return ReconciliarLiquidacionResultado(reconciliada=False)

        actuales, liquidacion_vigente = await self._aplicar_si_hay_diff(liquidacion, diff, locales)
        resto = await self._actualizar_periodo_estado_extra(
            liquidacion, liquidacion_vigente, cd_liq, actuales
        )
        return _resultado_no_terminal(diff, resto)

    async def _actualizar_periodo_estado_extra(
        self,
        liquidacion: Liquidacion,
        liquidacion_vigente: Liquidacion,
        cd_liq: CdLiquidacion,
        actuales: list[Incidente],
    ) -> tuple[bool, bool, bool, bool]:
        periodo_actualizado = await self._actualizar_periodo(
            liquidacion.id, liquidacion.periodo, actuales
        )
        estado_actualizado = await self._pisar_estado(liquidacion, cd_liq)
        extra_actualizado, factura_actualizada = await self._actualizar_extra_y_factura(
            liquidacion_vigente, cd_liq
        )
        return periodo_actualizado, estado_actualizado, extra_actualizado, factura_actualizada

    async def _aplicar_si_hay_diff(
        self, liquidacion: Liquidacion, diff: DiffIncidentes, locales: list[Incidente]
    ) -> tuple[list[Incidente], Liquidacion]:
        """Sin diff, no hay nada que aplicar — devuelve `locales`/`liquidacion`
        tal cual. Con diff, `_aplicar` ya deja persistido el nuevo total
        (incidentes + extra vigente); acá se arma la copia de `liquidacion`
        que lo refleja, para que el ajuste por extra que pueda correr después
        en la misma pasada parta de ese total, no del viejo."""
        if not (diff.altas or diff.cambios or diff.bajas):
            return locales, liquidacion
        nuevo_total = await self._aplicar(liquidacion, diff)
        actuales = await self._ports.incidentes.list_by_liquidacion(liquidacion.id)
        liquidacion_vigente = replace(
            liquidacion, total_importe=nuevo_total, total_incidentes=len(actuales)
        )
        return actuales, liquidacion_vigente

    async def _solo_estado_extra_y_factura(
        self, liquidacion: Liquidacion, cd_liq: CdLiquidacion
    ) -> ReconciliarLiquidacionResultado:
        """Liquidación terminal: nunca toca incidentes ni alertas. El estado
        solo puede avanzar aprobada→cerrada; cualquier otra cosa que reporte
        AyC (incluida una liquidación cerrada) se ignora."""
        estado_actualizado = await self._avanzar_a_cerrada(liquidacion, cd_liq)
        extra_actualizado, factura_actualizada = await self._actualizar_extra_y_factura(
            liquidacion, cd_liq
        )
        return ReconciliarLiquidacionResultado(
            reconciliada=True,
            estado_actualizado=estado_actualizado,
            extra_actualizado=extra_actualizado,
            factura_actualizada=factura_actualizada,
        )

    async def _avanzar_a_cerrada(self, liquidacion: Liquidacion, cd_liq: CdLiquidacion) -> bool:
        if liquidacion.estado != ESTADO_APROBADA:
            return False
        nuevo = estado_local_desde_ayc(estado_id=cd_liq.estado_id, nombre=cd_liq.estado)
        if nuevo != ESTADO_CERRADA:
            return False
        await self._ports.liquidaciones.update_estado(liquidacion.id, ESTADO_CERRADA)
        return True

    async def _aplicar(self, liquidacion: Liquidacion, diff: DiffIncidentes) -> float:
        if diff.bajas:
            await self._ports.incidentes.delete_by_ids(diff.bajas)
        if diff.cambios:
            await self._ports.incidentes.update_cobrados(diff.cambios)
        if diff.altas:
            await self._ports.incidentes.bulk_create(liquidacion.id, diff.altas)
        actuales = await self._ports.incidentes.list_by_liquidacion(liquidacion.id)
        nuevo_total = await self._actualizar_totales(liquidacion, actuales)
        await self._actualizar_tipo(liquidacion, actuales)
        await self._ports.reanalizar.execute(liquidacion.id)
        return nuevo_total

    async def _actualizar_tipo(self, liquidacion: Liquidacion, actuales: list[Incidente]) -> None:
        """Abono ⇄ regular según los incidentes ya reconciliados — antes del
        reanálisis, que filtra reglas por tipo (`reglas_aplicables`)."""
        tipo = tipo_segun_incidentes(actuales)
        if tipo != liquidacion.tipo_liquidacion:
            await self._ports.liquidaciones.update_tipo_liquidacion(liquidacion.id, tipo)

    async def _actualizar_totales(
        self, liquidacion: Liquidacion, actuales: list[Incidente]
    ) -> float:
        incidentes_costo_total = sum(i.costo_total_cobrado for i in actuales)
        total_importe = total_importe_con_incidentes_y_extra(
            incidentes_costo_total, liquidacion.monto_extra
        )
        await self._ports.liquidaciones.update_totales(liquidacion.id, len(actuales), total_importe)
        return total_importe

    async def _actualizar_periodo(
        self, liquidacion_id: UUID, periodo_actual: str, actuales: list[Incidente]
    ) -> bool:
        """Recalcula el período con las fechas de cierre ya reconciliadas — sin
        esto, una liquidación creada con incidentes todavía abiertos (período
        fijado por el fallback de `extraer_periodo`) queda con el período viejo
        para siempre aunque los incidentes cierren después en otro mes."""
        nuevo = periodo_mas_frecuente(i.fecha_cierre for i in actuales)
        if not nuevo or nuevo == periodo_actual:
            return False
        await self._ports.liquidaciones.update_periodo(liquidacion_id, nuevo)
        return True

    async def _actualizar_extra_y_factura(
        self, liquidacion: Liquidacion, cd_liq: CdLiquidacion
    ) -> tuple[bool, bool]:
        return await actualizar_extra_y_factura(
            self._ports.liquidaciones, self._ports.cd_gateway, liquidacion, cd_liq
        )

    async def _pisar_estado(self, liquidacion: Liquidacion, cd_liq: CdLiquidacion) -> bool:
        nuevo = estado_local_desde_ayc(estado_id=cd_liq.estado_id, nombre=cd_liq.estado)
        if nuevo is None or nuevo == liquidacion.estado:
            return False
        await self._ports.liquidaciones.update_estado(liquidacion.id, nuevo)
        return True


def _resultado_no_terminal(
    diff: DiffIncidentes, resto: tuple[bool, bool, bool, bool]
) -> ReconciliarLiquidacionResultado:
    periodo_actualizado, estado_actualizado, extra_actualizado, factura_actualizada = resto
    return ReconciliarLiquidacionResultado(
        reconciliada=True,
        altas=len(diff.altas),
        cambios=len(diff.cambios),
        bajas=len(diff.bajas),
        estado_actualizado=estado_actualizado,
        periodo_actualizado=periodo_actualizado,
        extra_actualizado=extra_actualizado,
        factura_actualizada=factura_actualizada,
    )
