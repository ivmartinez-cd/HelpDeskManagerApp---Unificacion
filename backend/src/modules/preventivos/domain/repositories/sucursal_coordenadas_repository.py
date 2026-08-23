from collections.abc import Sequence
from typing import Protocol

from src.modules.preventivos.domain.entities.sucursal_coordenadas import SucursalCoordenadas


class SucursalCoordenadasRepository(Protocol):
    async def list_by_siges_sucursal_ids(
        self, siges_sucursal_ids: Sequence[int]
    ) -> dict[int, SucursalCoordenadas]:
        """Solo las que ya están resueltas — sucursales sin fila no aparecen
        en el dict (a diferencia de un `None` explícito por id)."""
        ...

    async def upsert(self, coordenadas: SucursalCoordenadas) -> None: ...
