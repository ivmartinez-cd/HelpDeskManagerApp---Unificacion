"""Schemas del overview de estadísticas (contrato camelCase del legacy).

Las fechas viajan como `date`/`datetime` ISO en vez de los strings de SQLite; el
resto de los nombres de campo es idéntico a routers/estadisticas.py.
"""

from datetime import date

from pydantic import BaseModel, Field

from src.modules.insumos.application.dtos.statistics import StatisticsOverview
from src.modules.insumos.domain.services.statistics_series import DailyPoint
from src.modules.insumos.domain.value_objects.audit_statistics import (
    CustomerActivity,
    SkuCount,
)


class DailyPointOut(BaseModel):
    date: date
    created: int
    failed: int

    @classmethod
    def from_point(cls, point: DailyPoint) -> "DailyPointOut":
        return cls(date=point.day, created=point.created, failed=point.failed)


class CustomerStatOut(BaseModel):
    customer_id: int = Field(serialization_alias="customerId")
    customer_name: str = Field(serialization_alias="customerName")
    created: int
    failed: int
    total: int

    @classmethod
    def from_activity(cls, activity: CustomerActivity) -> "CustomerStatOut":
        return cls(
            customer_id=activity.customer_id,
            customer_name=activity.customer_name or "Sin nombre",
            created=activity.created,
            failed=activity.failed,
            total=activity.total,
        )


class SkuStatOut(BaseModel):
    sku: str
    description: str | None = None
    count: int

    @classmethod
    def from_count(cls, row: SkuCount) -> "SkuStatOut":
        return cls(sku=row.sku, description=row.description, count=row.count)


class EstadisticasResponse(BaseModel):
    days: int
    start_date: date = Field(serialization_alias="startDate")
    end_date: date = Field(serialization_alias="endDate")
    earliest_date: date | None = Field(default=None, serialization_alias="earliestDate")
    total_created: int = Field(serialization_alias="totalCreated")
    total_failed: int = Field(serialization_alias="totalFailed")
    previous_created: int = Field(serialization_alias="previousCreated")
    previous_start_date: date = Field(serialization_alias="previousStartDate")
    previous_end_date: date = Field(serialization_alias="previousEndDate")
    daily_average: float = Field(serialization_alias="dailyAverage")
    peak_day: date | None = Field(default=None, serialization_alias="peakDay")
    peak_day_count: int = Field(serialization_alias="peakDayCount")
    active_customers: int = Field(serialization_alias="activeCustomers")
    distinct_skus: int = Field(serialization_alias="distinctSkus")
    series: list[DailyPointOut]
    top_customers: list[CustomerStatOut] = Field(serialization_alias="topCustomers")
    top_skus: list[SkuStatOut] = Field(serialization_alias="topSkus")

    @classmethod
    def from_result(cls, result: StatisticsOverview) -> "EstadisticasResponse":
        period = result.period
        return cls(
            days=period.days,
            start_date=period.start,
            end_date=period.end,
            earliest_date=result.earliest_day,
            total_created=result.total_created,
            total_failed=result.total_failed,
            previous_created=result.previous_created,
            previous_start_date=period.previous_start,
            previous_end_date=period.previous_end,
            daily_average=result.daily_average,
            peak_day=result.peak_day,
            peak_day_count=result.peak_day_count,
            active_customers=result.active_customers,
            distinct_skus=result.distinct_skus,
            series=[DailyPointOut.from_point(p) for p in result.series],
            top_customers=[CustomerStatOut.from_activity(c) for c in result.top_customers],
            top_skus=[SkuStatOut.from_count(s) for s in result.top_skus],
        )
