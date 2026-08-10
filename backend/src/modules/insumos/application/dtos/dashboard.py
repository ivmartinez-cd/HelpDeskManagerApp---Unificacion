"""DTO de salida de GET /api/insumos/dashboard (mismo shape que el legacy)."""

from dataclasses import dataclass

from src.modules.insumos.domain.services.dashboard_summary import CustomerSummary


@dataclass(frozen=True)
class DashboardThresholds:
    critical: int
    urgent: int
    warning: int


@dataclass(frozen=True)
class DashboardResult:
    totals: dict[str, int]
    loaded_today: int
    customers_enabled: int
    per_customer: list[CustomerSummary]
    thresholds: DashboardThresholds
    refresh_minutes: int
