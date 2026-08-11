"""DTOs de salida de las estadísticas (GET /estadisticas y /estadisticas/clientes/{id}).

Los porcentajes y promedios ya vienen redondeados como los dejaba el legacy: la capa
HTTP solo renombra campos, no recalcula.
"""

from dataclasses import dataclass
from datetime import date, datetime

from src.modules.insumos.domain.services.statistics_series import DailyPoint
from src.modules.insumos.domain.value_objects.audit_statistics import (
    CustomerActivity,
    DeviceCount,
    FailureReasonCount,
    RecentFailure,
    SkuCount,
)
from src.modules.insumos.domain.value_objects.stats_range import StatsRange


@dataclass(frozen=True)
class StatisticsOverview:
    period: StatsRange
    earliest_day: date | None
    total_created: int
    total_failed: int
    previous_created: int
    daily_average: float
    peak_day: date | None
    peak_day_count: int
    active_customers: int
    distinct_skus: int
    series: list[DailyPoint]
    top_customers: list[CustomerActivity]
    top_skus: list[SkuCount]


@dataclass(frozen=True)
class FulfillmentWorst:
    created_at: datetime
    sku: str | None
    device_serial: str | None
    minutes: float


@dataclass(frozen=True)
class FulfillmentStats:
    """Tiempo de atención propio, en minutos hábiles."""

    measured: int
    total_created: int
    coverage_pct: float
    avg_minutes: float | None
    max_minutes: float | None
    worst: FulfillmentWorst | None
    work_hour_start: int
    work_hour_end: int


@dataclass(frozen=True)
class DispatchWorst:
    order_id: str
    sku: str | None
    device_serial: str | None
    days: float


@dataclass(frozen=True)
class PendingToDispatchStats:
    """Tránsito de Canal Directo (Pendiente → Despachado), en días corridos — no es
    tiempo de gestión propio, ver FulfillmentStats."""

    measured: int
    total_created: int
    coverage_pct: float
    avg_days: float | None
    max_days: float | None
    worst: DispatchWorst | None


@dataclass(frozen=True)
class CustomerStatistics:
    period: StatsRange
    customer_id: int
    customer_name: str
    earliest_day: date | None
    total_created: int
    total_failed: int
    success_rate: float
    previous_created: int
    previous_failed: int
    daily_average: float
    peak_day: date | None
    peak_day_count: int
    auto_created: int
    manual_created: int
    auto_pct: float
    monitored_devices: int
    distinct_skus: int
    fulfillment: FulfillmentStats
    pending_to_dispatch: PendingToDispatchStats
    series: list[DailyPoint]
    top_skus: list[SkuCount]
    top_devices: list[DeviceCount]
    failure_reasons: list[FailureReasonCount]
    recent_failures: list[RecentFailure]
