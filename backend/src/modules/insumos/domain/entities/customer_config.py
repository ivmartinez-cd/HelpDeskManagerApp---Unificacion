"""Cliente del padrón local (customers_config): qué clientes de Insight se monitorean."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerConfig:
    customer_id: int
    name: str
    enabled: bool = True
