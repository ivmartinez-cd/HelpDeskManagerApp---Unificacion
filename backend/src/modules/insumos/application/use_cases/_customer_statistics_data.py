"""Recolección de los agregados del detalle de cliente (una query por dimensión).

Separado del caso de uso para que este quede legible: acá solo hay I/O de lectura,
sin reglas de negocio.
"""

from dataclasses import dataclass
from datetime import date

from src.modules.insumos.domain.repositories.audit_statistics_repository import (
    AuditStatisticsRepository,
)
from src.modules.insumos.domain.repositories.known_device_repository import (
    KnownDeviceRepository,
)
from src.modules.insumos.domain.services.statistics_series import (
    DailyPoint,
    fill_daily_series,
)
from src.modules.insumos.domain.value_objects.audit_statistics import (
    DeviceCount,
    DispatchRow,
    FailureReasonCount,
    FulfillmentRow,
    RecentFailure,
    SkuCount,
    SourceSplit,
)
from src.modules.insumos.domain.value_objects.stats_range import StatsRange

TOP_DEVICES_LIMIT = 10
FAILURE_REASONS_LIMIT = 5
RECENT_FAILURES_LIMIT = 10


@dataclass(frozen=True)
class CustomerAggregates:
    series: list[DailyPoint]
    current: dict[str, int]
    previous: dict[str, int]
    top_skus: list[SkuCount]
    top_devices: list[DeviceCount]
    failure_reasons: list[FailureReasonCount]
    recent_failures: list[RecentFailure]
    source_split: SourceSplit
    fulfillment_rows: list[FulfillmentRow]
    dispatch_rows: list[DispatchRow]
    monitored_devices: int
    earliest_day: date | None


async def gather_customer_aggregates(
    stats: AuditStatisticsRepository,
    devices: KnownDeviceRepository,
    customer_id: int,
    period: StatsRange,
) -> CustomerAggregates:
    start, end = period.start, period.end
    counts = await stats.daily_counts(start, end, customer_id=customer_id)
    monitored = await devices.count_monitored_by_customer()
    return CustomerAggregates(
        series=fill_daily_series(start, end, counts),
        current=await stats.event_totals(start, end, customer_id=customer_id),
        previous=await stats.event_totals(
            period.previous_start, period.previous_end, customer_id=customer_id
        ),
        top_skus=await stats.top_skus(start, end, customer_id=customer_id),
        top_devices=await stats.top_devices(start, end, customer_id, TOP_DEVICES_LIMIT),
        failure_reasons=await stats.failure_reasons(
            start, end, customer_id, FAILURE_REASONS_LIMIT
        ),
        recent_failures=await stats.recent_failures(
            start, end, customer_id, RECENT_FAILURES_LIMIT
        ),
        source_split=await stats.source_split(start, end, customer_id),
        fulfillment_rows=await stats.fulfillment_rows(start, end, customer_id),
        dispatch_rows=await stats.dispatch_rows(start, end, customer_id),
        monitored_devices=monitored.get(customer_id, 0),
        earliest_day=await stats.earliest_day(),
    )
