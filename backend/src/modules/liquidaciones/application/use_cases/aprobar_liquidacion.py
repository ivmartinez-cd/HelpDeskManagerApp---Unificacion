"""Caso de uso AprobarLiquidacion — propaga estado "Aprobada" a wsAyC y actualiza local.

Orden de operaciones: SOAP primero, DB después. Si el SOAP falla → sin escritura
local, el error llega al usuario. Si el SOAP OK y la DB falla → estado inconsistente:
se loguea critical y se devuelve error con instrucciones para el usuario.
"""

import logging
from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.liquidacion import ESTADO_APROBADA, Liquidacion
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

_ESTADO_AYC = "Aprobada"


@dataclass(frozen=True)
class AprobarLiquidacionPorts:
    liquidaciones: LiquidacionRepository
    cd_gateway: CdLiquidacionesGateway


class AprobarLiquidacion:
    def __init__(self, ports: AprobarLiquidacionPorts) -> None:
        self._ports = ports

    async def execute(self, liquidacion_id: UUID, usuario: str) -> Liquidacion:
        liq = await self._ports.liquidaciones.get_by_id(liquidacion_id)
        if liq is None:
            raise NotFoundError(f"Liquidación {liquidacion_id} no encontrada")
        if not liq.numero_liquidacion:
            raise LiquidacionSinVinculoAyCError(liquidacion_id)

        ayc_id = int(liq.numero_liquidacion.split("-")[0])

        try:
            await self._ports.cd_gateway.set_estado(ayc_id, _ESTADO_AYC, usuario)
        except Exception as exc:
            raise LiquidacionAyCOperationError(
                f"No se pudo aprobar la liquidación {liq.numero_liquidacion} en wsAyC"
            ) from exc

        updated = await self._ports.liquidaciones.update_estado(liquidacion_id, ESTADO_APROBADA)
        if updated is None:
            logger.critical(
                "aprobar_liquidacion: SOAP OK pero fallo al actualizar estado local. "
                "liquidacion_id=%s numero=%s ayc_id=%d",
                liquidacion_id,
                liq.numero_liquidacion,
                ayc_id,
            )
            raise LiquidacionAyCOperationError(
                "La aprobación se ejecutó en wsAyC pero el estado local no se pudo "
                "actualizar. Recargá la liquidación — si el estado no cambió, "
                "contactar soporte."
            )
        return updated
