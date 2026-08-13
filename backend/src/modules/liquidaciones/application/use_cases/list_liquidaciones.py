"""Caso de uso ListLiquidaciones — port de GET /liquidaciones.

Todos los parámetros son opcionales: sin filtros devuelve todas las liquidaciones."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)


@dataclass(frozen=True)
class ListLiquidacionesPorts:
    liquidaciones: LiquidacionRepository


class ListLiquidaciones:
    def __init__(self, ports: ListLiquidacionesPorts) -> None:
        self._ports = ports

    async def execute(
        self,
        prestador_id: UUID | None = None,
        estado: str | None = None,
        periodo: str | None = None,
    ) -> list[Liquidacion]:
        return await self._ports.liquidaciones.list_filtered(
            prestador_id=prestador_id, estado=estado, periodo=periodo
        )
