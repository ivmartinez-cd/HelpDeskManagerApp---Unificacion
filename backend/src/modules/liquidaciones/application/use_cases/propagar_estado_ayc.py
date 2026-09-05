"""Base de los casos de uso que propagan un cambio de estado a wsAyC
(`setLiquidationStatus`) y luego lo reflejan en la liquidación local:
`ObservarLiquidacion` (Observada) y `RecibirLiquidacion` (Recibida). Aprobar
tiene su propio caso de uso porque además notifica por mail.

Orden deliberado: primero AyC, después local. Si AyC falla no se toca nada; si
AyC anduvo y el update local falla, se loguea crítico y se avisa al usuario —
el estado real ya cambió en Canal Directo y la próxima reconciliación lo trae.
"""

import logging
from dataclasses import dataclass
from typing import ClassVar
from uuid import UUID

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion
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
from src.modules.liquidaciones.domain.services.transiciones_ayc import validar_transicion
from src.shared.domain.errors import NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PropagarEstadoAyCPorts:
    liquidaciones: LiquidacionRepository
    cd_gateway: CdLiquidacionesGateway


class PropagarEstadoAyC:
    """Subclases fijan `estado` (constante local, ver `estados_ayc.py`) y
    `verbo` (para los mensajes de error: "observar", "recibir")."""

    estado: ClassVar[str]
    verbo: ClassVar[str]

    def __init__(self, ports: PropagarEstadoAyCPorts) -> None:
        self._ports = ports

    async def execute(self, liquidacion_id: UUID, usuario: str) -> Liquidacion:
        liq = await self._ports.liquidaciones.get_by_id(liquidacion_id)
        if liq is None:
            raise NotFoundError(f"Liquidación {liquidacion_id} no encontrada")
        if not liq.numero_liquidacion:
            raise LiquidacionSinVinculoAyCError(liquidacion_id)
        validar_transicion(self.verbo, liq.estado)
        ayc_id = int(liq.numero_liquidacion.split("-")[0])
        try:
            await self._ports.cd_gateway.set_estado(ayc_id, self.estado, usuario)
        except Exception as exc:
            raise LiquidacionAyCOperationError(
                f"No se pudo {self.verbo} la liquidación {liq.numero_liquidacion} en wsAyC"
            ) from exc
        return await self._reflejar_local(liq, ayc_id)

    async def _reflejar_local(self, liq: Liquidacion, ayc_id: int) -> Liquidacion:
        updated = await self._ports.liquidaciones.update_estado(liq.id, self.estado)
        if updated is None:
            logger.critical(
                "%s_liquidacion: SOAP OK pero fallo al actualizar estado local. "
                "liquidacion_id=%s numero=%s ayc_id=%d",
                self.verbo,
                liq.id,
                liq.numero_liquidacion,
                ayc_id,
            )
            raise LiquidacionAyCOperationError(
                f"El cambio a {self.estado} se ejecutó en wsAyC pero el estado local no se "
                "pudo actualizar. Recargá la liquidación — si el estado no cambió, "
                "contactar soporte."
            )
        return updated
