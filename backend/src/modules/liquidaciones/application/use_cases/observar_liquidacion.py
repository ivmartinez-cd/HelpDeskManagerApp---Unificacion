"""Caso de uso ObservarLiquidacion — propaga estado "Observada" a wsAyC y actualiza local.

El motivo de la observación no se persiste ni se envía a AyC: `setLiquidationStatus`
no tiene parámetro de texto, y las entidades Observacion existentes son del motor de
reglas (ALT005), no para notas manuales de la TL.
"""

import logging
from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.liquidacion import ESTADO_OBSERVADA, Liquidacion
from src.modules.liquidaciones.domain.exceptions import (
    LiquidacionAyCOperationError,
    LiquidacionSinVinculoAyCError,
)
from src.modules.liquidaciones.domain.repositories.cd_liquidaciones_gateway import (
    CdLiquidacionesGateway,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.shared.domain.errors import NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ObservarLiquidacionPorts:
    liquidaciones: LiquidacionRepository
    cd_gateway: CdLiquidacionesGateway


class ObservarLiquidacion:
    def __init__(self, ports: ObservarLiquidacionPorts) -> None:
        self._ports = ports

    async def execute(self, liquidacion_id: UUID, usuario: str) -> Liquidacion:
        liq = await self._ports.liquidaciones.get_by_id(liquidacion_id)
        if liq is None:
            raise NotFoundError(f"Liquidación {liquidacion_id} no encontrada")
        if not liq.numero_liquidacion:
            raise LiquidacionSinVinculoAyCError(liquidacion_id)

        ayc_id = int(liq.numero_liquidacion.split("-")[0])

        try:
            await self._ports.cd_gateway.set_estado(ayc_id, ESTADO_OBSERVADA, usuario)
        except Exception as exc:
            raise LiquidacionAyCOperationError(
                f"No se pudo observar la liquidación {liq.numero_liquidacion} en wsAyC"
            ) from exc

        updated = await self._ports.liquidaciones.update_estado(liquidacion_id, ESTADO_OBSERVADA)
        if updated is None:
            logger.critical(
                "observar_liquidacion: SOAP OK pero fallo al actualizar estado local. "
                "liquidacion_id=%s numero=%s ayc_id=%d",
                liquidacion_id,
                liq.numero_liquidacion,
                ayc_id,
            )
            raise LiquidacionAyCOperationError(
                "La observación se ejecutó en wsAyC pero el estado local no se pudo "
                "actualizar. Recargá la liquidación — si el estado no cambió, "
                "contactar soporte."
            )
        return updated
