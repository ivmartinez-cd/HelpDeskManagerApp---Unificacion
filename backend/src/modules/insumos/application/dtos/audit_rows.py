"""DTO de una fila del Historial (GET /api/insumos/audit)."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AuditRow:
    audit_id: int
    event: str
    created_at: datetime | None
    hp_request_id: int | None = None
    device_id: int | None = None
    customer_id: int | None = None
    customer_name: str | None = None
    device_serial: str | None = None
    sku: str | None = None
    description: str | None = None
    internal_order_id: str | None = None
    order_type: str = "supply"
    detail: str | None = None
    dry_run: bool = False
    hp_request_time: datetime | None = None
    initial_percent_left: int | None = None
    initial_days_left: int | None = None
    initial_pages_left: int | None = None
    supply_url: str | None = None
    action: str | None = None
