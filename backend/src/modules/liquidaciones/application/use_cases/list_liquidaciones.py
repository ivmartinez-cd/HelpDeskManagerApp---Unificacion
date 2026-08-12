"""Caso de uso ListLiquidaciones — port de GET /liquidaciones.

`prestador_id=None` devuelve todas (vista global del dashboard/listado);
`prestador_id=<UUID>` filtra por prestador (legacy: siempre era requerido)."""

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

    async def execute(self, prestador_id: UUID | None) -> list[Liquidacion]:
        if prestador_id is None:
            return await self._ports.liquidaciones.list_all()
        return await self._ports.liquidaciones.list_by_prestador(prestador_id)
