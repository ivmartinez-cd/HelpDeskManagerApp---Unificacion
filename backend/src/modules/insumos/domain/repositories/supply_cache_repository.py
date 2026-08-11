"""Puerto del cache local de supplies (tabla supply_serial_cache).

Alimentado por el scan incremental y sembrado inmediatamente al crear un pedido —
es la ÚNICA fuente que ve pedidos de origen Interno para el chequeo anti-duplicados
hasta que el scan los confirme.
"""

from collections.abc import Sequence
from typing import Protocol

from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, SupplyStatusEvent


class SupplyCacheRepository(Protocol):
    async def upsert(self, entries: Sequence[CachedSupply]) -> None:
        """Inserta/actualiza por supply_id. Ante conflicto: serial/estado/fecha se pisan
        siempre; empresa_id/sku/description solo si el valor nuevo no es vacío (mismo
        criterio que el legacy — el scan puede traer menos datos que la creación).

        Además registra en supply_status_history el primer avistaje de cada estado
        distinto (dedup por (supply_id, estado)) — sin whitelist: un estado real
        desconocido no debe perderse en silencio (ver cd_state.py)."""
        ...

    async def get_by_serial(self, serial: str, limit: int = 20) -> list[CachedSupply]:
        """Últimas entradas para el serial (case-insensitive), supply_id DESC."""
        ...

    async def find_active_by_serial(self, serial: str) -> CachedSupply | None:
        """El supply activo más reciente de la serie (excluye Entregado/Anulado/
        Cancelado) — insumo del bloqueo 2 de /load."""
        ...

    async def get_status(self, supply_id: int) -> str | None:
        """Estado cacheado de un supply por su ID numérico (None si no está en cache)."""
        ...

    async def get_statuses_batch(self, supply_ids: Sequence[int]) -> dict[int, str]:
        """{supply_id: estado} para los que están en cache — una sola query."""
        ...

    async def get_recently_cached_ids(
        self, supply_ids: Sequence[int], within_seconds: int
    ) -> set[int]:
        """Subset cacheado hace menos de `within_seconds` — TTL para no re-verificar
        por SOAP en cada carga del dashboard."""
        ...

    async def get_noncancelled_by_serials(
        self, serials: Sequence[str]
    ) -> dict[str, list[CachedSupply]]:
        """Entradas no Anuladas/Canceladas por serie (keyed serial.upper(), supply_id
        DESC) — una sola query para todas las series pendientes (anti N+1)."""
        ...

    async def get_status_history_batch(
        self, supply_ids: Sequence[int]
    ) -> dict[int, list[SupplyStatusEvent]]:
        """{supply_id: eventos en orden cronológico} desde supply_status_history —
        una sola query para todos los IDs, nunca un loop por fila."""
        ...
