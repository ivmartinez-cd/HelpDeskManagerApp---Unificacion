"""Factories del módulo insumos: un `build_*` por caso de uso.

Repartidas por área para que ningún archivo se pase del máximo de líneas; el
punto de importación sigue siendo único (`presentation.dependencies`). Las piezas
compartidas (gateways, settings de pedido, zona horaria) viven en `wiring.py`.
"""

from src.modules.insumos.presentation.dependencies.config import (
    build_get_insumos_config,
    build_save_insumos_config,
)
from src.modules.insumos.presentation.dependencies.mail_log import (
    build_list_mail_log,
)
from src.modules.insumos.presentation.dependencies.requests import (
    build_cancel_order,
    build_dismiss_request,
    build_get_availability_windows,
    build_get_consumable_detail,
    build_get_consumable_history,
    build_get_consumable_request_history,
    build_get_dashboard,
    build_get_device_supplies,
    build_list_audit,
    build_list_pending_orders,
    build_list_requests,
    build_load_order,
    build_reconcile_order,
)
from src.modules.insumos.presentation.dependencies.statistics import (
    build_get_customer_statistics,
    build_get_statistics_overview,
)

__all__ = [
    "build_cancel_order",
    "build_dismiss_request",
    "build_get_availability_windows",
    "build_get_consumable_detail",
    "build_get_consumable_history",
    "build_get_consumable_request_history",
    "build_get_customer_statistics",
    "build_get_dashboard",
    "build_get_device_supplies",
    "build_get_insumos_config",
    "build_get_statistics_overview",
    "build_list_audit",
    "build_list_mail_log",
    "build_list_pending_orders",
    "build_list_requests",
    "build_load_order",
    "build_reconcile_order",
    "build_save_insumos_config",
]
