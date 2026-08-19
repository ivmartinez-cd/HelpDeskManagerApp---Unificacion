"""ActualizarEstadoLocal — cambia el estado de una liquidación SIN vínculo AyC.

Liquidaciones vinculadas (`numero_liquidacion` no nulo) tienen su estado
gobernado por AyC — lo pisa la reconciliación automática (ADR-024) o los
botones Aprobar/Observar/Anular, nunca este selector. Solo llega a existir una
liquidación local sin vínculo por import CSV/Excel manual.
"""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion
from src.modules.liquidaciones.domain.exceptions import LiquidacionConVinculoAycError
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.shared.domain.errors import NotFoundError


@dataclass(frozen=True)
class ActualizarEstadoLocalPorts:
    liquidaciones: LiquidacionRepository


class ActualizarEstadoLocal:
    def __init__(self, ports: ActualizarEstadoLocalPorts) -> None:
        self._ports = ports

    async def execute(self, liquidacion_id: UUID, estado: str) -> Liquidacion:
        liq = await self._ports.liquidaciones.get_by_id(liquidacion_id)
        if liq is None:
            raise NotFoundError(f"Liquidación {liquidacion_id} no encontrada")
        if liq.numero_liquidacion:
            raise LiquidacionConVinculoAycError(liquidacion_id)

        updated = await self._ports.liquidaciones.update_estado(liquidacion_id, estado)
        assert updated is not None  # get_by_id ya confirmó que existe
        return updated
