"""Caso de uso GetStatisticsOverview — port de GET /api/estadisticas.

Agregación en vivo por SQL sobre order_audit para el rango pedido, sin pre-cálculo ni
índices adicionales: el volumen es de cientos/miles de filas y el rango es arbitrario.
"""

from dataclasses import dataclass
from datetime import date, datetime, tzinfo

from src.modules.insumos.application.dtos.statistics import StatisticsOverview
from src.modules.insumos.domain.entities.audit_record import EVENT_CREATED, EVENT_FAILED
from src.modules.insumos.domain.repositories.audit_statistics_repository import (
    AuditStatisticsRepository,
)
from src.modules.insumos.domain.services.statistics_series import (
    DailyPoint,
    fill_daily_series,
    peak_of,
)
from src.modules.insumos.domain.value_objects.audit_statistics import (
    CustomerActivity,
    SkuCount,
)
from src.modules.insumos.domain.value_objects.stats_range import (
    StatsRange,
    resolve_stats_range,
)

TOP_LIMIT = 10


@dataclass(frozen=True)
class GetStatisticsOverviewPorts:
    stats: AuditStatisticsRepository


@dataclass(frozen=True)
class _Aggregates:
    series: list[DailyPoint]
    current: dict[str, int]
    previous: dict[str, int]
    customers: list[CustomerActivity]
    skus: list[SkuCount]
    earliest_day: date | None


class GetStatisticsOverview:
    def __init__(self, ports: GetStatisticsOverviewPorts, timezone: tzinfo) -> None:
        self._ports = ports
        # "Hoy" es el día calendario argentino, no el día UTC del contenedor.
        self._timezone = timezone

    async def execute(
        self,
        days: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> StatisticsOverview:
        period = resolve_stats_range(
            days, start_date, end_date, today=datetime.now(self._timezone).date()
        )
        return _build(period, await self._gather(period))

    async def _gather(self, period: StatsRange) -> _Aggregates:
        stats = self._ports.stats
        counts = await stats.daily_counts(period.start, period.end)
        return _Aggregates(
            series=fill_daily_series(period.start, period.end, counts),
            current=await stats.event_totals(period.start, period.end),
            previous=await stats.event_totals(period.previous_start, period.previous_end),
            customers=await stats.customer_activity(period.start, period.end),
            skus=await stats.top_skus(period.start, period.end),
            earliest_day=await stats.earliest_day(),
        )


def _build(period: StatsRange, data: _Aggregates) -> StatisticsOverview:
    total_created = data.current.get(EVENT_CREATED, 0)
    peak_day, peak_day_count = peak_of(data.series, total_created)
    return StatisticsOverview(
        period=period,
        earliest_day=data.earliest_day,
        total_created=total_created,
        total_failed=data.current.get(EVENT_FAILED, 0),
        previous_created=data.previous.get(EVENT_CREATED, 0),
        daily_average=round(total_created / period.days, 1),
        peak_day=peak_day,
        peak_day_count=peak_day_count,
        # Clientes activos y SKUs distintos son el universo completo del rango; los
        # rankings que viajan son solo el top 10 de ese universo.
        active_customers=len(data.customers),
        distinct_skus=len(data.skus),
        series=data.series,
        top_customers=data.customers[:TOP_LIMIT],
        top_skus=data.skus[:TOP_LIMIT],
    )
