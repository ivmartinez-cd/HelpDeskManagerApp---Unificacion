"""Schema del Historial (GET /api/insumos/audit) — mismo contrato snake_case que el
legacy (routers/audit.py::AuditRow), con fechas ISO en vez de strings de SQLite."""

from datetime import datetime

from pydantic import BaseModel

from src.modules.insumos.application.dtos.audit_rows import AuditRow


class AuditRowOut(BaseModel):
    id: int
    event: str
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
    dry_run: bool
    hp_request_time: datetime | None = None
    initial_percent_left: int | None = None
    initial_days_left: int | None = None
    initial_pages_left: int | None = None
    supply_url: str | None = None
    created_at: datetime | None = None
    action: str | None = None

    @classmethod
    def from_row(cls, row: AuditRow) -> "AuditRowOut":
        return cls(
            id=row.audit_id,
            event=row.event,
            hp_request_id=row.hp_request_id,
            device_id=row.device_id,
            customer_id=row.customer_id,
            customer_name=row.customer_name,
            device_serial=row.device_serial,
            sku=row.sku,
            description=row.description,
            internal_order_id=row.internal_order_id,
            order_type=row.order_type,
            detail=row.detail,
            dry_run=row.dry_run,
            hp_request_time=row.hp_request_time,
            initial_percent_left=row.initial_percent_left,
            initial_days_left=row.initial_days_left,
            initial_pages_left=row.initial_pages_left,
            supply_url=row.supply_url,
            created_at=row.created_at,
            action=row.action,
        )
