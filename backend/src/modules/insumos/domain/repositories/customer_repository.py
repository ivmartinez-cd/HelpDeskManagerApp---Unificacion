"""Puerto de customers_config."""

from typing import Protocol

from src.modules.insumos.domain.value_objects.zone_contacts import Customer


class CustomerRepository(Protocol):
    async def list_all(self) -> list[Customer]: ...

    async def set_enabled(self, customer_id: int, enabled: bool) -> None: ...

    async def bulk_toggle(self, enabled: bool) -> None: ...

    async def sync(self, customers: list[dict[str, object]]) -> None:
        """Upsert de nombre; nunca pisa el flag `enabled`."""
        ...
