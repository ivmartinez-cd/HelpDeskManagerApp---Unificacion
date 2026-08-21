"""ReconciliarLiquidacion — colaborador de SincronizarLiquidaciones.

Actualiza in-place los incidentes de una liquidación que ya existe localmente
cuando AyC reporta cambios (costos, km, y los campos descriptivos que consume el
motor de reglas), pisa su `estado` con el que reporta AyC y trae su ítem extra y
número de factura (`Extra`/`DetalleExtra`/`FacturaLocal`/`FacturaNro` de
`getLiquidationById`, P4) cuando AyC tiene alguno cargado — la contraparte de
`_procesar` en `sincronizar_liquidaciones.py`, que solo crea liquidaciones
nuevas.

Una liquidación en estado terminal (aprobada/cerrada) nunca reconcilia
incidentes/alertas ni pisa su `estado` — eso queda congelado para siempre
(decisión consciente: no reabrir liquidaciones ya cerradas). El extra/factura
es la excepción: en la práctica AyC suele cargar la factura en el mismo
momento en que aprueba la liquidación, así que si también se lo bloqueara acá
ese dato nunca llegaría a sincronizarse (hallazgo 2026-08-21, liquidaciones
3905-7/3929-7 aprobadas/cerradas sin factura local pese a tenerla en AyC) — una
liquidación terminal sigue trayendo extra/factura vía `_solo_extra_y_factura`,
sin tocar nada más.

Orden fijo dentro de una liquidación: bajas → cambios → altas → recálculo de
totales → reanálisis → pisar estado → traer extra/factura. El motor de reglas
corre sobre el set de incidentes ya reconciliado, antes de pisar estado y traer
el extra/factura (ninguno de los dos afecta al motor) — si reanalizara antes de
las bajas, regeneraría alertas para incidentes que está por borrar. El estado se
pisa con el que reportaba AyC *antes* de reconciliar los incidentes (`cd_liq`,
no se vuelve a consultar) — evaluar el guard de estado terminal contra el estado
local previo, no el nuevo, así una liquidación recién marcada `aprobada` en AyC
también recibe esta última reconciliación de incidentes.

Nunca borra y recrea un incidente que sigue existiendo remotamente (`cambios`
hace UPDATE in-place, preserva `incidente_id`) — ver
`domain/services/reconciliar_incidentes.py` para el porqué (`alertas.incidente_id`
es `ON DELETE CASCADE`; recrear el incidente se llevaría el triage de la TL).
"""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
)
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
from src.modules.liquidaciones.domain.services.reconciliar_incidentes import (
    DiffIncidentes,
    reconciliar_incidentes,
)
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import (
    CdLiquidacion,
    CdLiquidacionDetalle,
)
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
    extra_actualizado: bool = False
    factura_actualizada: bool = False


class ReconciliarLiquidacion:
    def __init__(self, ports: ReconciliarLiquidacionPorts) -> None:
        self._ports = ports

    async def execute(
        self, liquidacion: Liquidacion, cd_liq: CdLiquidacion, remotos: list[IncidenteImportado]
    ) -> ReconciliarLiquidacionResultado:
        if liquidacion.estado in _ESTADOS_TERMINALES:
            return await self._solo_extra_y_factura(liquidacion, cd_liq)
        if len(remotos) != cd_liq.cant_incidentes:
            return ReconciliarLiquidacionResultado(reconciliada=False)

        locales = await self._ports.incidentes.list_by_liquidacion(liquidacion.id)
        diff = reconciliar_incidentes(locales, remotos)
        if locales and len(diff.bajas) / len(locales) > _UMBRAL_BAJAS_MASIVAS:
            return ReconciliarLiquidacionResultado(reconciliada=False)

        if diff.altas or diff.cambios or diff.bajas:
            await self._aplicar(liquidacion.id, diff)
        estado_actualizado = await self._pisar_estado(liquidacion, cd_liq)
        extra_actualizado, factura_actualizada = await self._actualizar_extra_y_factura(
            liquidacion, cd_liq
        )
        return ReconciliarLiquidacionResultado(
            reconciliada=True,
            altas=len(diff.altas),
            cambios=len(diff.cambios),
            bajas=len(diff.bajas),
            estado_actualizado=estado_actualizado,
            extra_actualizado=extra_actualizado,
            factura_actualizada=factura_actualizada,
        )

    async def _solo_extra_y_factura(
        self, liquidacion: Liquidacion, cd_liq: CdLiquidacion
    ) -> ReconciliarLiquidacionResultado:
        """Liquidación terminal: nunca toca incidentes, alertas ni `estado`
        (`_pisar_estado` ni se llama), solo intenta traer extra/factura."""
        extra_actualizado, factura_actualizada = await self._actualizar_extra_y_factura(
            liquidacion, cd_liq
        )
        return ReconciliarLiquidacionResultado(
            reconciliada=True,
            extra_actualizado=extra_actualizado,
            factura_actualizada=factura_actualizada,
        )

    async def _aplicar(self, liquidacion_id: UUID, diff: DiffIncidentes) -> None:
        if diff.bajas:
            await self._ports.incidentes.delete_by_ids(diff.bajas)
        if diff.cambios:
            await self._ports.incidentes.update_cobrados(diff.cambios)
        if diff.altas:
            await self._ports.incidentes.bulk_create(liquidacion_id, diff.altas)
        await self._actualizar_totales(liquidacion_id)
        await self._ports.reanalizar.execute(liquidacion_id)

    async def _actualizar_totales(self, liquidacion_id: UUID) -> None:
        actuales = await self._ports.incidentes.list_by_liquidacion(liquidacion_id)
        total_importe = round(sum(i.costo_total_cobrado for i in actuales), 2)
        await self._ports.liquidaciones.update_totales(
            liquidacion_id, len(actuales), total_importe
        )

    async def _actualizar_extra_y_factura(
        self, liquidacion: Liquidacion, cd_liq: CdLiquidacion
    ) -> tuple[bool, bool]:
        """Una sola llamada a `get_detalle` cubre ambos campos. Nunca borra un
        ítem extra cargado a mano cuando AyC no tiene ninguno (`concepto_extra`/
        `monto_extra` en `None`): la carga manual sigue siendo el fallback
        acordado con la TL (P4). El número de factura no tiene contraparte
        manual — si AyC no la reporta (`numero_factura=None`), no hay nada que
        pisar."""
        detalle = await self._ports.cd_gateway.get_detalle(cd_liq.id)
        if detalle is None:
            return False, False
        extra_actualizado = await self._actualizar_extra(liquidacion, detalle)
        factura_actualizada = await self._actualizar_factura(liquidacion, detalle)
        return extra_actualizado, factura_actualizada

    async def _actualizar_extra(
        self, liquidacion: Liquidacion, detalle: CdLiquidacionDetalle
    ) -> bool:
        if detalle.monto_extra is None:
            return False
        if (
            detalle.concepto_extra == liquidacion.concepto_extra
            and detalle.monto_extra == liquidacion.monto_extra
        ):
            return False
        await self._ports.liquidaciones.update_extra(
            liquidacion.id, detalle.concepto_extra, detalle.monto_extra
        )
        return True

    async def _actualizar_factura(
        self, liquidacion: Liquidacion, detalle: CdLiquidacionDetalle
    ) -> bool:
        if detalle.numero_factura is None or detalle.numero_factura == liquidacion.numero_factura:
            return False
        await self._ports.liquidaciones.update_numero_factura(
            liquidacion.id, detalle.numero_factura
        )
        return True

    async def _pisar_estado(self, liquidacion: Liquidacion, cd_liq: CdLiquidacion) -> bool:
        nuevo = estado_local_desde_ayc(estado_id=cd_liq.estado_id, nombre=cd_liq.estado)
        if nuevo is None or nuevo == liquidacion.estado:
            return False
        await self._ports.liquidaciones.update_estado(liquidacion.id, nuevo)
        return True
