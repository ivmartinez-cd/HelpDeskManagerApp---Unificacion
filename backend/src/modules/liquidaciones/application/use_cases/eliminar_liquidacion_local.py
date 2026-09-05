"""EliminarLiquidacionLocal — borra localmente una liquidación.

Liquidaciones vinculadas a Canal Directo (`numero_liquidacion` no nulo) no se
pueden borrar así sin más: el registro local quedaría desincronizado de AyC
(la próxima sincronización la recrearía como "nueva", perdiendo todo el
triage de alertas/observaciones ya hecho). El camino correcto es `/anular`,
que primero anula en AyC. `forzar=True` es la única excepción deliberada — la
usa el botón "Eliminar solo localmente" cuando `/anular` ya falló del lado de
AyC y alguien decide igual limpiar el registro local a mano.
"""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.errors import LiquidacionNoEncontradaError
from src.modules.liquidaciones.domain.exceptions import LiquidacionConVinculoAycError
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)


@dataclass(frozen=True)
class EliminarLiquidacionLocalPorts:
    liquidaciones: LiquidacionRepository


class EliminarLiquidacionLocal:
    def __init__(self, ports: EliminarLiquidacionLocalPorts) -> None:
        self._ports = ports

    async def execute(self, liquidacion_id: UUID, *, forzar: bool = False) -> None:
        liq = await self._ports.liquidaciones.get_by_id(liquidacion_id)
        if liq is None:
            raise LiquidacionNoEncontradaError(liquidacion_id)
        if liq.numero_liquidacion and not forzar:
            raise LiquidacionConVinculoAycError(liquidacion_id)

        deleted = await self._ports.liquidaciones.delete(liquidacion_id)
        assert deleted  # get_by_id ya confirmó que existe
