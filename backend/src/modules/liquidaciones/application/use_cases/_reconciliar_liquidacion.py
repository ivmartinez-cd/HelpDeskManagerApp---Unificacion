"""ReconciliarLiquidacion — colaborador de SincronizarLiquidaciones.

Actualiza in-place los incidentes de una liquidación que ya existe localmente
cuando AyC reporta cambios (costos, km, y los campos descriptivos que consume el
motor de reglas) y pisa su `estado` con el que reporta AyC — la contraparte de
`_procesar` en `sincronizar_liquidaciones.py`, que solo crea liquidaciones
nuevas. Nunca se llama para liquidaciones en estado terminal (aprobada/cerrada):
esas quedan congeladas, ni se les pide el detalle SOAP.

Orden fijo dentro de una liquidación: bajas → cambios → altas → recálculo de
totales → pisar estado → reanálisis. El motor de reglas corre al final, sobre
el set de incidentes ya reconciliado — si reanalizara antes de las bajas,
regeneraría alertas para incidentes que está por borrar. El estado se pisa con
el que reportaba AyC *antes* de reconciliar los incidentes (`cd_liq`, no se
vuelve a consultar) — evaluar el guard de estado terminal contra el estado
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


@dataclass(frozen=True)
class ReconciliarLiquidacionResultado:
    reconciliada: bool
    altas: int = 0
    cambios: int = 0
    bajas: int = 0
    estado_actualizado: bool = False


class ReconciliarLiquidacion:
    def __init__(self, ports: ReconciliarLiquidacionPorts) -> None:
        self._ports = ports

    async def execute(
        self, liquidacion: Liquidacion, cd_liq: CdLiquidacion, remotos: list[IncidenteImportado]
    ) -> ReconciliarLiquidacionResultado:
        if liquidacion.estado in _ESTADOS_TERMINALES:
            return ReconciliarLiquidacionResultado(reconciliada=False)
        if len(remotos) != cd_liq.cant_incidentes:
            return ReconciliarLiquidacionResultado(reconciliada=False)

        locales = await self._ports.incidentes.list_by_liquidacion(liquidacion.id)
        diff = reconciliar_incidentes(locales, remotos)
        if locales and len(diff.bajas) / len(locales) > _UMBRAL_BAJAS_MASIVAS:
            return ReconciliarLiquidacionResultado(reconciliada=False)

        if diff.altas or diff.cambios or diff.bajas:
            await self._aplicar(liquidacion.id, diff)
        estado_actualizado = await self._pisar_estado(liquidacion, cd_liq)
        return ReconciliarLiquidacionResultado(
            reconciliada=True,
            altas=len(diff.altas),
            cambios=len(diff.cambios),
            bajas=len(diff.bajas),
            estado_actualizado=estado_actualizado,
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

    async def _pisar_estado(self, liquidacion: Liquidacion, cd_liq: CdLiquidacion) -> bool:
        nuevo = estado_local_desde_ayc(estado_id=cd_liq.estado_id, nombre=cd_liq.estado)
        if nuevo is None or nuevo == liquidacion.estado:
            return False
        await self._ports.liquidaciones.update_estado(liquidacion.id, nuevo)
        return True
