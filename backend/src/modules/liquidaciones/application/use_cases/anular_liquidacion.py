"""Caso de uso AnularLiquidacion — anula en wsAyC y elimina el registro local.

"Anular" en AyC = voidLiquidation: el registro queda marcado en AyC, no borrado
físicamente. Localmente se borra porque una liquidación anulada no tiene workflow
útil en nuestra app.
"""

import logging
from dataclasses import dataclass
from uuid import UUID

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
from src.modules.liquidaciones.domain.services.transiciones_ayc import validar_anulable
from src.shared.domain.errors import NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnularLiquidacionPorts:
    liquidaciones: LiquidacionRepository
    cd_gateway: CdLiquidacionesGateway


class AnularLiquidacion:
    def __init__(self, ports: AnularLiquidacionPorts) -> None:
        self._ports = ports

    async def execute(self, liquidacion_id: UUID) -> None:
        liq = await self._ports.liquidaciones.get_by_id(liquidacion_id)
        if liq is None:
            raise NotFoundError(f"Liquidación {liquidacion_id} no encontrada")
        if not liq.numero_liquidacion:
            raise LiquidacionSinVinculoAyCError(liquidacion_id)
        validar_anulable(liq.estado)

        ayc_id = int(liq.numero_liquidacion.split("-")[0])

        try:
            await self._ports.cd_gateway.void_liquidacion(ayc_id)
        except Exception as exc:
            raise LiquidacionAyCOperationError(
                f"No se pudo anular la liquidación {liq.numero_liquidacion} en wsAyC"
            ) from exc

        deleted = await self._ports.liquidaciones.delete(liquidacion_id)
        if not deleted:
            logger.critical(
                "anular_liquidacion: SOAP OK pero fallo al eliminar registro local. "
                "liquidacion_id=%s numero=%s ayc_id=%d",
                liquidacion_id,
                liq.numero_liquidacion,
                ayc_id,
            )
            raise LiquidacionAyCOperationError(
                "La anulación se ejecutó en wsAyC pero el registro local no se pudo "
                "eliminar. Recargá el listado — si la liquidación sigue visible, "
                "contactar soporte."
            )
