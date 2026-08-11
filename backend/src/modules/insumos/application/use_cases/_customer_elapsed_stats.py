"""Traducción de los resúmenes de tiempo del dominio a los DTOs del detalle de cliente.

`coverage_pct` sale sobre el total de CREATED del período (no sobre `measured`): es
justamente el dato que evita leer el promedio como si aplicara a todos los pedidos.
"""

from dataclasses import dataclass

from src.modules.insumos.application.dtos.statistics import (
    DispatchWorst,
    FulfillmentStats,
    FulfillmentWorst,
    PendingToDispatchStats,
)
from src.modules.insumos.domain.services.fulfillment_stats import ElapsedSummary
from src.modules.insumos.domain.value_objects.audit_statistics import (
    DispatchRow,
    FulfillmentRow,
)


@dataclass(frozen=True)
class ElapsedPair:
    fulfillment: FulfillmentStats
    pending_to_dispatch: PendingToDispatchStats


def to_fulfillment_stats(
    summary: ElapsedSummary, total_created: int, work_hour_start: int, work_hour_end: int
) -> FulfillmentStats:
    return FulfillmentStats(
        measured=summary.measured,
        total_created=total_created,
        coverage_pct=_coverage_pct(summary.measured, total_created),
        avg_minutes=_rounded(summary.average),
        max_minutes=_rounded(summary.maximum),
        worst=_fulfillment_worst(summary),
        work_hour_start=work_hour_start,
        work_hour_end=work_hour_end,
    )


def to_pending_to_dispatch_stats(
    summary: ElapsedSummary, total_created: int
) -> PendingToDispatchStats:
    return PendingToDispatchStats(
        measured=summary.measured,
        total_created=total_created,
        coverage_pct=_coverage_pct(summary.measured, total_created),
        avg_days=_rounded(summary.average),
        max_days=_rounded(summary.maximum),
        worst=_dispatch_worst(summary),
    )


def _fulfillment_worst(summary: ElapsedSummary) -> FulfillmentWorst | None:
    if summary.worst is None or not isinstance(summary.worst.row, FulfillmentRow):
        return None
    row = summary.worst.row
    return FulfillmentWorst(
        created_at=row.created_at,
        sku=row.sku,
        device_serial=row.device_serial,
        minutes=round(summary.worst.value, 1),
    )


def _dispatch_worst(summary: ElapsedSummary) -> DispatchWorst | None:
    if summary.worst is None or not isinstance(summary.worst.row, DispatchRow):
        return None
    row = summary.worst.row
    return DispatchWorst(
        order_id=row.internal_order_id,
        sku=row.sku,
        device_serial=row.device_serial,
        days=round(summary.worst.value, 1),
    )


def _coverage_pct(measured: int, total_created: int) -> float:
    return round(100 * measured / total_created, 1) if total_created else 0.0


def _rounded(value: float | None) -> float | None:
    return round(value, 1) if value is not None else None
