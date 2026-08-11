"""Schemas de GET /api/insumos/dashboard (mismo shape camelCase que el legacy)."""

from pydantic import BaseModel, Field

from src.modules.insumos.application.dtos.dashboard import DashboardResult
from src.modules.insumos.domain.services.dashboard_summary import CustomerSummary


class CustomerSummaryOut(BaseModel):
    customer_id: int = Field(serialization_alias="customerId")
    name: str
    pending: int
    critical: int
    urgent: int
    warning: int
    good: int
    loaded: int
    error: str | None = None

    @classmethod
    def from_summary(cls, summary: CustomerSummary) -> "CustomerSummaryOut":
        return cls(
            customer_id=summary.customer_id,
            name=summary.name,
            pending=summary.pending,
            critical=summary.critical,
            urgent=summary.urgent,
            warning=summary.warning,
            good=summary.good,
            loaded=summary.loaded,
            error=summary.error,
        )


class ThresholdsOut(BaseModel):
    critical: int
    urgent: int
    warning: int


class DashboardResponse(BaseModel):
    totals: dict[str, int]
    loaded_today: int = Field(serialization_alias="loadedToday")
    customers_enabled: int = Field(serialization_alias="customersEnabled")
    per_customer: list[CustomerSummaryOut] = Field(serialization_alias="perCustomer")
    thresholds: ThresholdsOut
    refresh_minutes: int = Field(serialization_alias="refreshMinutes")

    @classmethod
    def from_result(cls, result: DashboardResult) -> "DashboardResponse":
        return cls(
            totals=result.totals,
            loaded_today=result.loaded_today,
            customers_enabled=result.customers_enabled,
            per_customer=[CustomerSummaryOut.from_summary(s) for s in result.per_customer],
            thresholds=ThresholdsOut(
                critical=result.thresholds.critical,
                urgent=result.thresholds.urgent,
                warning=result.thresholds.warning,
            ),
            refresh_minutes=result.refresh_minutes,
        )
