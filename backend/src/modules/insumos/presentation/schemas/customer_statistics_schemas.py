"""Schemas del detalle de estadísticas por cliente (contrato camelCase del legacy)."""

from datetime import date, datetime
from typing import TypedDict

from pydantic import BaseModel, Field

from src.modules.insumos.application.dtos.statistics import (
    CustomerStatistics,
    FulfillmentStats,
    PendingToDispatchStats,
)
from src.modules.insumos.domain.value_objects.audit_statistics import (
    DeviceCount,
    FailureReasonCount,
    RecentFailure,
)
from src.modules.insumos.presentation.schemas.statistics_schemas import (
    DailyPointOut,
    SkuStatOut,
)


class DeviceStatOut(BaseModel):
    device_serial: str = Field(serialization_alias="deviceSerial")
    count: int

    @classmethod
    def from_count(cls, row: DeviceCount) -> "DeviceStatOut":
        return cls(device_serial=row.device_serial, count=row.count)


class FailureReasonOut(BaseModel):
    reason: str
    count: int
    last_at: datetime = Field(serialization_alias="lastAt")

    @classmethod
    def from_count(cls, row: FailureReasonCount) -> "FailureReasonOut":
        return cls(reason=row.reason, count=row.count, last_at=row.last_at)


class RecentFailureOut(BaseModel):
    created_at: datetime = Field(serialization_alias="createdAt")
    sku: str | None = None
    device_serial: str | None = Field(default=None, serialization_alias="deviceSerial")
    detail: str | None = None

    @classmethod
    def from_failure(cls, row: RecentFailure) -> "RecentFailureOut":
        return cls(
            created_at=row.created_at,
            sku=row.sku,
            device_serial=row.device_serial,
            detail=row.detail,
        )


class FulfillmentWorstOut(BaseModel):
    created_at: datetime = Field(serialization_alias="createdAt")
    sku: str | None = None
    device_serial: str | None = Field(default=None, serialization_alias="deviceSerial")
    minutes: float


class FulfillmentStatsOut(BaseModel):
    measured: int
    total_created: int = Field(serialization_alias="totalCreated")
    coverage_pct: float = Field(serialization_alias="coveragePct")
    avg_minutes: float | None = Field(default=None, serialization_alias="avgMinutes")
    max_minutes: float | None = Field(default=None, serialization_alias="maxMinutes")
    worst: FulfillmentWorstOut | None = None
    work_hour_start: int = Field(serialization_alias="workHourStart")
    work_hour_end: int = Field(serialization_alias="workHourEnd")

    @classmethod
    def from_stats(cls, stats: FulfillmentStats) -> "FulfillmentStatsOut":
        worst = stats.worst
        return cls(
            measured=stats.measured,
            total_created=stats.total_created,
            coverage_pct=stats.coverage_pct,
            avg_minutes=stats.avg_minutes,
            max_minutes=stats.max_minutes,
            worst=FulfillmentWorstOut(
                created_at=worst.created_at,
                sku=worst.sku,
                device_serial=worst.device_serial,
                minutes=worst.minutes,
            )
            if worst
            else None,
            work_hour_start=stats.work_hour_start,
            work_hour_end=stats.work_hour_end,
        )


class PendingToDispatchWorstOut(BaseModel):
    order_id: str = Field(serialization_alias="orderId")
    sku: str | None = None
    device_serial: str | None = Field(default=None, serialization_alias="deviceSerial")
    days: float


class PendingToDispatchStatsOut(BaseModel):
    measured: int
    total_created: int = Field(serialization_alias="totalCreated")
    coverage_pct: float = Field(serialization_alias="coveragePct")
    avg_days: float | None = Field(default=None, serialization_alias="avgDays")
    max_days: float | None = Field(default=None, serialization_alias="maxDays")
    worst: PendingToDispatchWorstOut | None = None

    @classmethod
    def from_stats(cls, stats: PendingToDispatchStats) -> "PendingToDispatchStatsOut":
        worst = stats.worst
        return cls(
            measured=stats.measured,
            total_created=stats.total_created,
            coverage_pct=stats.coverage_pct,
            avg_days=stats.avg_days,
            max_days=stats.max_days,
            worst=PendingToDispatchWorstOut(
                order_id=worst.order_id,
                sku=worst.sku,
                device_serial=worst.device_serial,
                days=worst.days,
            )
            if worst
            else None,
        )


class CustomerDetailResponse(BaseModel):
    customer_id: int = Field(serialization_alias="customerId")
    customer_name: str = Field(serialization_alias="customerName")
    days: int
    start_date: date = Field(serialization_alias="startDate")
    end_date: date = Field(serialization_alias="endDate")
    earliest_date: date | None = Field(default=None, serialization_alias="earliestDate")
    previous_start_date: date = Field(serialization_alias="previousStartDate")
    previous_end_date: date = Field(serialization_alias="previousEndDate")
    total_created: int = Field(serialization_alias="totalCreated")
    total_failed: int = Field(serialization_alias="totalFailed")
    success_rate: float = Field(serialization_alias="successRate")
    previous_created: int = Field(serialization_alias="previousCreated")
    previous_failed: int = Field(serialization_alias="previousFailed")
    daily_average: float = Field(serialization_alias="dailyAverage")
    peak_day: date | None = Field(default=None, serialization_alias="peakDay")
    peak_day_count: int = Field(serialization_alias="peakDayCount")
    auto_created: int = Field(serialization_alias="autoCreated")
    manual_created: int = Field(serialization_alias="manualCreated")
    auto_pct: float = Field(serialization_alias="autoPct")
    monitored_devices: int = Field(serialization_alias="monitoredDevices")
    distinct_skus: int = Field(serialization_alias="distinctSkus")
    fulfillment: FulfillmentStatsOut
    pending_to_dispatch: PendingToDispatchStatsOut = Field(
        serialization_alias="pendingToDispatch"
    )
    series: list[DailyPointOut]
    top_skus: list[SkuStatOut] = Field(serialization_alias="topSkus")
    top_devices: list[DeviceStatOut] = Field(serialization_alias="topDevices")
    failure_reasons: list[FailureReasonOut] = Field(serialization_alias="failureReasons")
    recent_failures: list[RecentFailureOut] = Field(serialization_alias="recentFailures")

    @classmethod
    def from_result(cls, result: CustomerStatistics) -> "CustomerDetailResponse":
        return cls(
            **_scalars(result),
            fulfillment=FulfillmentStatsOut.from_stats(result.fulfillment),
            pending_to_dispatch=PendingToDispatchStatsOut.from_stats(
                result.pending_to_dispatch
            ),
            series=[DailyPointOut.from_point(p) for p in result.series],
            top_skus=[SkuStatOut.from_count(s) for s in result.top_skus],
            top_devices=[DeviceStatOut.from_count(d) for d in result.top_devices],
            failure_reasons=[
                FailureReasonOut.from_count(f) for f in result.failure_reasons
            ],
            recent_failures=[
                RecentFailureOut.from_failure(f) for f in result.recent_failures
            ],
        )


class _ScalarFields(TypedDict):
    """Los campos planos del detalle, separados solo para que `from_result` quepa —
    tipado explícito (y no dict[str, object]) para que el `**` siga siendo chequeable."""

    customer_id: int
    customer_name: str
    days: int
    start_date: date
    end_date: date
    earliest_date: date | None
    previous_start_date: date
    previous_end_date: date
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


def _scalars(result: CustomerStatistics) -> _ScalarFields:
    period = result.period
    return {
        "customer_id": result.customer_id,
        "customer_name": result.customer_name,
        "days": period.days,
        "start_date": period.start,
        "end_date": period.end,
        "earliest_date": result.earliest_day,
        "previous_start_date": period.previous_start,
        "previous_end_date": period.previous_end,
        "total_created": result.total_created,
        "total_failed": result.total_failed,
        "success_rate": result.success_rate,
        "previous_created": result.previous_created,
        "previous_failed": result.previous_failed,
        "daily_average": result.daily_average,
        "peak_day": result.peak_day,
        "peak_day_count": result.peak_day_count,
        "auto_created": result.auto_created,
        "manual_created": result.manual_created,
        "auto_pct": result.auto_pct,
        "monitored_devices": result.monitored_devices,
        "distinct_skus": result.distinct_skus,
    }
