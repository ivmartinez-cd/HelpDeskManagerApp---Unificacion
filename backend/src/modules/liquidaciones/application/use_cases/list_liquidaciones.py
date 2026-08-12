"""Caso de uso ListLiquidaciones — port de GET /liquidaciones (filtrado por
prestador; el legacy lo hacía opcional, acá se exige a propósito hasta que exista una
vista real "todos los prestadores" que lo necesite — ver YAGNI, ARCHITECTURE_GUIDE §1)."""

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

    async def execute(self, prestador_id: UUID) -> list[Liquidacion]:
        return await self._ports.liquidaciones.list_by_prestador(prestador_id)
