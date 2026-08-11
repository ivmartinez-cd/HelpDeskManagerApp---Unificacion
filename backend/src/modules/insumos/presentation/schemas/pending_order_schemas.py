"""Schema de GET /api/insumos/orders/pending — contrato camelCase del legacy
(pending_orders.py::PendingOrderRow), con fechas ISO en vez de strings de SQLite."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.modules.insumos.application.dtos.pending_orders import PendingOrderRow
from src.modules.insumos.domain.value_objects.cd_supply import SupplyStatusEvent


class SupplyStatusEventOut(BaseModel):
    """Un estado del pedido en CD y cuándo la app lo detectó por primera vez — no el
    momento exacto de la transición real (CD no lo expone)."""

    estado: str
    at: datetime

    @classmethod
    def from_event(cls, event: SupplyStatusEvent) -> "SupplyStatusEventOut":
        return cls(estado=event.estado, at=event.first_seen_at)


class PendingOrderRowOut(BaseModel):
    hp_request_id: int = Field(serialization_alias="hpRequestId")
    customer_id: int = Field(serialization_alias="customerId")
    customer_name: str | None = Field(default=None, serialization_alias="customerName")
    device_id: int = Field(serialization_alias="deviceId")
    serial: str
    store: str
    sku: str
    description: str
    order_id: str = Field(serialization_alias="orderId")
    supply_url: str | None = Field(default=None, serialization_alias="supplyUrl")
    supply_status: str = Field(serialization_alias="supplyStatus")
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")
    initial_percent_left: int | None = Field(
        default=None, serialization_alias="initialPercentLeft"
    )
    initial_days_left: int | None = Field(default=None, serialization_alias="initialDaysLeft")
    initial_pages_left: int | None = Field(default=None, serialization_alias="initialPagesLeft")
    current_percent_left: int | None = Field(
        default=None, serialization_alias="currentPercentLeft"
    )
    current_days_left: int | None = Field(default=None, serialization_alias="currentDaysLeft")
    current_pages_left: int | None = Field(default=None, serialization_alias="currentPagesLeft")
    status_key: str | None = Field(default=None, serialization_alias="statusKey")
    status_label: str | None = Field(default=None, serialization_alias="statusLabel")
    status_history: list[SupplyStatusEventOut] = Field(
        default_factory=list, serialization_alias="statusHistory"
    )

    @classmethod
    def from_row(cls, row: PendingOrderRow) -> "PendingOrderRowOut":
        fields = {
            name: getattr(row, name) for name in cls.model_fields if name != "status_history"
        }
        return cls(
            status_history=[SupplyStatusEventOut.from_event(e) for e in row.status_history],
            **fields,
        )
