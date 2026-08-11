"""Schemas de alertas de solicitudes sin cargar — contrato camelCase del legacy
(routers/alerts.py::AlertRow), con fechas ISO en vez de strings de SQLite."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.insumos.domain.entities.request_alert import RequestAlert


class AlertRowOut(BaseModel):
    hp_request_id: int = Field(serialization_alias="hpRequestId")
    customer_id: int | None = Field(default=None, serialization_alias="customerId")
    customer_name: str = Field(serialization_alias="customerName")
    device_serial: str = Field(serialization_alias="deviceSerial")
    sku: str
    description: str
    requested_at: datetime | None = Field(default=None, serialization_alias="requestedAt")
    first_seen_at: datetime = Field(serialization_alias="firstSeenAt")
    escalated_at: datetime | None = Field(default=None, serialization_alias="escalatedAt")

    @classmethod
    def from_alert(cls, alert: RequestAlert) -> "AlertRowOut":
        return cls(
            hp_request_id=alert.hp_request_id,
            customer_id=alert.customer_id,
            customer_name=alert.customer_name,
            device_serial=alert.device_serial,
            sku=alert.sku,
            description=alert.description,
            requested_at=alert.requested_at,
            first_seen_at=alert.first_seen_at,
            escalated_at=alert.escalated_at,
        )


class AcknowledgeRequestBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    hp_request_ids: list[int] = Field(default_factory=list, alias="hpRequestIds")


class AcknowledgeResponse(BaseModel):
    ok: bool
    acknowledged: int
