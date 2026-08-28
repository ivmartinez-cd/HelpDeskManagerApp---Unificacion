"""Factories del módulo insumos: un `build_*` por caso de uso.

Repartidas por área para que ningún archivo se pase del máximo de líneas; el
punto de importación sigue siendo único (`presentation.dependencies`). Las piezas
compartidas (gateways, settings de pedido, zona horaria) viven en `wiring.py`.
"""

from src.modules.insumos.presentation.dependencies.alerts import (
    build_acknowledge_alerts,
    build_list_alerts,
)
from src.modules.insumos.presentation.dependencies.audit import (
    build_get_audit_summary,
    build_list_audit,
)
from src.modules.insumos.presentation.dependencies.backfill import (
    build_backfill_consumable_serial,
)
from src.modules.insumos.presentation.dependencies.config import (
    build_get_insumos_config,
    build_save_insumos_config,
)
from src.modules.insumos.presentation.dependencies.customers import (
    build_apply_zone_contacts_import,
    build_bulk_seed_contacts,
    build_bulk_toggle_customers,
    build_delete_zone_contact,
    build_get_customer_zones,
    build_get_sds_contacts,
    build_get_zone_contacts,
    build_import_contacts_from_supply,
    build_list_customers,
    build_preview_zone_contacts_import,
    build_set_client_mail_enabled,
    build_set_zone_contact,
    build_sync_customers,
    build_toggle_customer,
)
from src.modules.insumos.presentation.dependencies.mail_log import (
    build_list_mail_log,
)
from src.modules.insumos.presentation.dependencies.new_devices import (
    build_count_new_devices,
    build_dismiss_new_device,
    build_list_new_devices,
    build_sync_new_devices,
)
from src.modules.insumos.presentation.dependencies.offline_devices import (
    build_count_offline_candidates,
    build_delete_offline_devices,
    build_dismiss_offline_device,
    build_list_offline_devices,
    build_list_offline_outages,
    build_sync_monitor_status,
    build_verify_offline_devices,
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
    build_ignore_request,
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
    "build_acknowledge_alerts",
    "build_apply_zone_contacts_import",
    "build_backfill_consumable_serial",
    "build_bulk_seed_contacts",
    "build_bulk_toggle_customers",
    "build_cancel_order",
    "build_count_new_devices",
    "build_count_offline_candidates",
    "build_delete_offline_devices",
    "build_delete_zone_contact",
    "build_dismiss_new_device",
    "build_dismiss_offline_device",
    "build_dismiss_request",
    "build_get_audit_summary",
    "build_get_availability_windows",
    "build_get_consumable_detail",
    "build_get_consumable_history",
    "build_get_consumable_request_history",
    "build_get_customer_statistics",
    "build_get_customer_zones",
    "build_get_dashboard",
    "build_get_device_supplies",
    "build_get_insumos_config",
    "build_get_sds_contacts",
    "build_get_statistics_overview",
    "build_get_zone_contacts",
    "build_ignore_request",
    "build_import_contacts_from_supply",
    "build_list_alerts",
    "build_list_audit",
    "build_list_customers",
    "build_list_mail_log",
    "build_list_new_devices",
    "build_list_offline_devices",
    "build_list_offline_outages",
    "build_list_pending_orders",
    "build_list_requests",
    "build_load_order",
    "build_preview_zone_contacts_import",
    "build_reconcile_order",
    "build_save_insumos_config",
    "build_set_client_mail_enabled",
    "build_set_zone_contact",
    "build_sync_customers",
    "build_sync_monitor_status",
    "build_sync_new_devices",
    "build_toggle_customer",
    "build_verify_offline_devices",
]
