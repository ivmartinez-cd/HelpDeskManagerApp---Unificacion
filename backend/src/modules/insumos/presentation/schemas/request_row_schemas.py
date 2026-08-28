"""Schema de fila de GET /api/insumos/requests (contrato camelCase del legacy)."""

from pydantic import BaseModel, Field

from src.modules.insumos.application.dtos.request_rows import RequestRow


class RequestRowOut(BaseModel):
    request_id: int = Field(serialization_alias="requestId")
    device_id: int = Field(serialization_alias="deviceId")
    customer_id: int | None = Field(default=None, serialization_alias="customerId")
    customer_name: str | None = Field(default=None, serialization_alias="customerName")
    store: str
    serial: str
    description: str
    sku: str
    percent_left: float | None = Field(default=None, serialization_alias="percentLeft")
    days_left: int = Field(serialization_alias="daysLeft")
    pages_left: int | None = Field(default=None, serialization_alias="pagesLeft")
    consumable_index: int | None = Field(default=None, serialization_alias="consumableIndex")
    consumable_url: str = Field(serialization_alias="consumableUrl")
    time: str
    raw_time: str | None = Field(default=None, serialization_alias="rawTime")
    status_key: str = Field(serialization_alias="statusKey")
    status_label: str = Field(serialization_alias="statusLabel")
    order_id: str | None = Field(default=None, serialization_alias="orderId")
    requested_percent: float | None = Field(default=None, serialization_alias="requestedPercent")
    requested_days_left: int | None = Field(
        default=None, serialization_alias="requestedDaysLeft"
    )
    last_contact: str | None = Field(default=None, serialization_alias="lastContact")
    days_offline: int | None = Field(default=None, serialization_alias="daysOffline")
    is_stale_offline: bool = Field(serialization_alias="isStaleOffline")
    validation_pending: bool = Field(serialization_alias="validationPending")
    validation_deadline: str | None = Field(
        default=None, serialization_alias="validationDeadline"
    )
    validation_swap_note: str | None = Field(
        default=None, serialization_alias="validationSwapNote"
    )
    validation_diagnosis_headline: str | None = Field(
        default=None, serialization_alias="validationDiagnosisHeadline"
    )
    validation_diagnosis_detail: str | None = Field(
        default=None, serialization_alias="validationDiagnosisDetail"
    )
    supply_id: str | None = Field(default=None, serialization_alias="supplyId")
    supply_url: str | None = Field(default=None, serialization_alias="supplyUrl")
    supply_status: str | None = Field(default=None, serialization_alias="supplyStatus")
    supply_fecha: str | None = Field(default=None, serialization_alias="supplyFecha")
    requiere_cambio_sucursal: bool = Field(serialization_alias="requiereCambioSucursal")
    sucursal_entrega: str | None = Field(default=None, serialization_alias="sucursalEntrega")
    observacion_zona: str | None = Field(default=None, serialization_alias="observacionZona")
    colour: str | None = None
    reused_consumable_note: str | None = Field(
        default=None, serialization_alias="reusedConsumableNote"
    )

    @classmethod
    def from_row(cls, row: RequestRow) -> "RequestRowOut":
        fields = {name: getattr(row, name) for name in cls.model_fields}
        return cls(**fields)
