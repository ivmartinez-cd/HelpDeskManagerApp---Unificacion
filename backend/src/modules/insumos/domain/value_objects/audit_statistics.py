"""Agregados crudos de order_audit que alimentan las estadísticas.

Son el contrato del puerto AuditStatisticsRepository: filas ya agrupadas por SQL
(la agregación se hace en la base, no en Python), salvo las dos series de tiempos
(fulfillment / pending→despachado) que se calculan en dominio porque dependen de
horario laboral y de supply_status_history.
"""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class DailyEventCount:
    day: date
    event: str
    count: int


@dataclass(frozen=True)
class CustomerActivity:
    customer_id: int
    customer_name: str | None
    created: int
    failed: int
    total: int


@dataclass(frozen=True)
class SkuCount:
    sku: str
    description: str | None
    count: int


@dataclass(frozen=True)
class DeviceCount:
    device_serial: str
    count: int


@dataclass(frozen=True)
class FailureReasonCount:
    reason: str
    count: int
    last_at: datetime


@dataclass(frozen=True)
class RecentFailure:
    created_at: datetime
    sku: str | None
    device_serial: str | None
    detail: str | None


@dataclass(frozen=True)
class SourceSplit:
    """Auto-cargados vs. total de CREATED — el resto son manuales."""

    auto: int
    total: int


@dataclass(frozen=True)
class FulfillmentRow:
    """Un CREATED con los dos instantes que definen el tiempo de atención."""

    sku: str | None
    device_serial: str | None
    hp_request_time: datetime
    created_at: datetime


@dataclass(frozen=True)
class DispatchRow:
    """Un CREATED de insumo con el pedido de Canal Directo que generó."""

    sku: str | None
    device_serial: str | None
    internal_order_id: str
    created_at: datetime
