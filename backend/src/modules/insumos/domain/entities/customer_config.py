"""Cliente del padrón local (customers_config): qué clientes de Insight se monitorean."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerConfig:
    customer_id: int
    name: str
    enabled: bool = True
    # Opt-in de aviso por mail al cliente cuando se carga su pedido (ver
    # domain/value_objects/client_order_notice.py). Arranca apagado para toda la
    # cartera — se activa a mano por cliente desde Clientes.
    client_mail_enabled: bool = False
