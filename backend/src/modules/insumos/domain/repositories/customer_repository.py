"""Puerto de customers_config."""

from typing import Protocol

from src.modules.insumos.domain.value_objects.zone_contacts import Customer


class CustomerRepository(Protocol):
    async def list_all(self) -> list[Customer]: ...

    async def set_enabled(self, customer_id: int, enabled: bool) -> None: ...

    async def bulk_toggle(self, enabled: bool) -> None: ...

    async def set_client_mail_enabled(self, customer_id: int, enabled: bool) -> None: ...

    async def is_client_mail_enabled(self, customer_id: int) -> bool:
        """False si el cliente no existe — usado por el flujo de carga antes de avisar
        por mail al cliente (ver client_order_notice.py)."""
        ...

    async def sync(self, customers: list[dict[str, object]]) -> None:
        """Upsert de nombre; nunca pisa el flag `enabled`."""
        ...
