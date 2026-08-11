"""Puerto de customers_config (padrón local de clientes monitoreados)."""

from collections.abc import Sequence
from typing import Protocol

from src.modules.insumos.domain.entities.customer_config import CustomerConfig


class CustomerConfigRepository(Protocol):
    async def list_enabled(self) -> list[CustomerConfig]:
        """Clientes habilitados para monitoreo, en el orden del padrón."""
        ...

    async def get_names(self) -> dict[int, str]:
        """{customer_id: nombre} de TODO el padrón, habilitado o no — un pedido en
        tránsito de un cliente deshabilitado después no debe quedar sin nombre."""
        ...

    async def sync_discovered(self, customers: Sequence[CustomerConfig]) -> None:
        """Registra clientes nuevos de Insight y refresca el nombre de los existentes.

        Los nuevos entran DESHABILITADOS: habilitar a un cliente lo mete en la
        auto-carga real, eso lo decide una persona, nunca un sync. Y el `enabled` de
        los que ya estaban nunca se toca."""
        ...
