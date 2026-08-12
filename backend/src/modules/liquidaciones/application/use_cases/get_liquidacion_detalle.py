"""Caso de uso GetLiquidacionDetalle — port de GET /liquidaciones/{id} (más el
detalle de incidentes/alertas/observaciones que el legacy resolvía con relaciones
ORM cargadas perezosamente; acá se piden explícitas)."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.dtos.liquidacion_detalle import LiquidacionDetalle
from src.modules.liquidaciones.domain.errors import LiquidacionNoEncontradaError
from src.modules.liquidaciones.domain.repositories.alerta_repository import AlertaRepository
from src.modules.liquidaciones.domain.repositories.incidente_repository import (
    IncidenteRepository,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.modules.liquidaciones.domain.repositories.observacion_repository import (
    ObservacionRepository,
)


@dataclass(frozen=True)
class GetLiquidacionDetallePorts:
    liquidaciones: LiquidacionRepository
    incidentes: IncidenteRepository
    alertas: AlertaRepository
    observaciones: ObservacionRepository


class GetLiquidacionDetalle:
    def __init__(self, ports: GetLiquidacionDetallePorts) -> None:
        self._ports = ports

    async def execute(self, liquidacion_id: UUID) -> LiquidacionDetalle:
        liquidacion = await self._ports.liquidaciones.get_by_id(liquidacion_id)
        if liquidacion is None:
            raise LiquidacionNoEncontradaError(liquidacion_id)
        return LiquidacionDetalle(
            liquidacion=liquidacion,
            incidentes=await self._ports.incidentes.list_by_liquidacion(liquidacion_id),
            alertas=await self._ports.alertas.list_by_liquidacion(liquidacion_id),
            observaciones=await self._ports.observaciones.list_by_liquidacion(liquidacion_id),
        )
