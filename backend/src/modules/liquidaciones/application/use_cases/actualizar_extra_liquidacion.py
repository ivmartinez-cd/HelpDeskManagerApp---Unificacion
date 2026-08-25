"""ActualizarExtraLiquidacion — PATCH manual del ítem extra de una liquidación.

Recalcula `total_importe` para que el extra quede reflejado ahí (ver
`recalcular_total_extra`) — antes este endpoint llamaba directo al repositorio
desde presentation (saltándose la capa de aplicación) y nunca tocaba el total,
el mismo bug que en la reconciliación automática (hallazgo real: liquidación
3907-5, San Juan)."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.modules.liquidaciones.domain.services.recalcular_total_extra import (
    total_importe_tras_cambiar_extra,
)
from src.shared.domain.errors import NotFoundError


@dataclass(frozen=True)
class ActualizarExtraLiquidacionPorts:
    liquidaciones: LiquidacionRepository


class ActualizarExtraLiquidacion:
    def __init__(self, ports: ActualizarExtraLiquidacionPorts) -> None:
        self._ports = ports

    async def execute(
        self, liquidacion_id: UUID, concepto_extra: str | None, monto_extra: float | None
    ) -> Liquidacion:
        liq = await self._ports.liquidaciones.get_by_id(liquidacion_id)
        if liq is None:
            raise NotFoundError(f"Liquidación {liquidacion_id} no encontrada")

        nuevo_total = total_importe_tras_cambiar_extra(liq, monto_extra)
        await self._ports.liquidaciones.update_totales(
            liquidacion_id, liq.total_incidentes, nuevo_total
        )
        updated = await self._ports.liquidaciones.update_extra(
            liquidacion_id, concepto_extra, monto_extra
        )
        assert updated is not None  # get_by_id ya confirmó que existe
        return updated
