"""Puerto del cache local de supplies (tabla supply_serial_cache).

Alimentado por el scan incremental y sembrado inmediatamente al crear un pedido —
es la ÚNICA fuente que ve pedidos de origen Interno para el chequeo anti-duplicados
hasta que el scan los confirme.
"""

from collections.abc import Sequence
from typing import Protocol

from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply


class SupplyCacheRepository(Protocol):
    async def upsert(self, entries: Sequence[CachedSupply]) -> None:
        """Inserta/actualiza por supply_id. Ante conflicto: serial/estado/fecha se pisan
        siempre; empresa_id/sku/description solo si el valor nuevo no es vacío (mismo
        criterio que el legacy — el scan puede traer menos datos que la creación)."""
        ...

    async def get_by_serial(self, serial: str, limit: int = 20) -> list[CachedSupply]:
        """Últimas entradas para el serial (case-insensitive), supply_id DESC."""
        ...
