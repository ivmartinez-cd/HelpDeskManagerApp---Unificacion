"""Puerto de customers_config (padrón local de clientes monitoreados)."""

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
