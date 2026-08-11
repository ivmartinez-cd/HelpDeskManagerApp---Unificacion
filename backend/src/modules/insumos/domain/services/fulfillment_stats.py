"""Dos métricas de tiempo distintas sobre los pedidos creados de un cliente.

- `compute_fulfillment`: tiempo de atención NUESTRO (minutos hábiles entre el momento
  en que HP registró la solicitud y el momento en que la app cargó el pedido).
- `compute_pending_to_dispatch`: tiempo de tránsito de CANAL DIRECTO (días corridos,
  no horas hábiles, entre Pendiente y el primer avistaje de Despachado) — no es
  gestión propia, por eso no se mide en horario laboral.

Ambas devuelven `measured` para no mentir con el promedio: los pedidos que no se
pudieron medir quedan afuera, nunca se les inventa un valor.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, tzinfo

from src.modules.insumos.domain.services.business_hours import business_minutes_between
from src.modules.insumos.domain.value_objects.audit_statistics import (
    DispatchRow,
    FulfillmentRow,
)
from src.modules.insumos.domain.value_objects.cd_state import DESPACHADO
from src.modules.insumos.domain.value_objects.cd_supply import SupplyStatusEvent

_SECONDS_PER_DAY = 86400.0


@dataclass(frozen=True)
class MeasuredWorst:
    row: FulfillmentRow | DispatchRow
    value: float


@dataclass(frozen=True)
class ElapsedSummary:
    measured: int
    average: float | None
    maximum: float | None
    worst: MeasuredWorst | None


def compute_fulfillment(
    rows: Iterable[FulfillmentRow],
    *,
    timezone: tzinfo,
    work_hour_start: int,
    work_hour_end: int,
) -> ElapsedSummary:
    """Minutos hábiles por pedido. Descarta los deltas negativos (desfasaje del reloj
    de HP) para no sesgar el promedio hacia abajo."""
    measured: list[tuple[FulfillmentRow, float]] = []
    for row in rows:
        if row.created_at < row.hp_request_time:
            continue
        minutes = business_minutes_between(
            row.hp_request_time.astimezone(timezone),
            row.created_at.astimezone(timezone),
            work_hour_start,
            work_hour_end,
        )
        measured.append((row, minutes))
    return _summarize(measured)


def compute_pending_to_dispatch(
    rows: Iterable[DispatchRow],
    history_by_supply: Mapping[int, Sequence[SupplyStatusEvent]],
) -> ElapsedSummary:
    """Días corridos hasta Despachado. `created_at` ES el momento en que el pedido
    entró a Pendiente: persistNewSupply siempre lo siembra en ese estado."""
    measured: list[tuple[DispatchRow, float]] = []
    for row in rows:
        supply_id = supply_id_of(row.internal_order_id)
        if supply_id is None:
            continue
        dispatched_at = _first_dispatch(history_by_supply.get(supply_id, ()))
        if dispatched_at is None or dispatched_at < row.created_at:
            continue
        elapsed = (dispatched_at - row.created_at).total_seconds() / _SECONDS_PER_DAY
        measured.append((row, elapsed))
    return _summarize(measured)


def supply_id_of(internal_order_id: str) -> int | None:
    """"441770-3" → 441770. None si no es parseable (incidentes, dry-runs)."""
    try:
        return int(internal_order_id.split("-")[0])
    except (ValueError, IndexError):
        return None


def _first_dispatch(events: Sequence[SupplyStatusEvent]) -> datetime | None:
    for event in events:
        if event.estado == DESPACHADO:
            return event.first_seen_at
    return None


def _summarize(
    measured: Sequence[tuple[FulfillmentRow, float] | tuple[DispatchRow, float]],
) -> ElapsedSummary:
    if not measured:
        return ElapsedSummary(measured=0, average=None, maximum=None, worst=None)
    values = [value for _, value in measured]
    worst_row, worst_value = max(measured, key=lambda pair: pair[1])
    return ElapsedSummary(
        measured=len(values),
        average=sum(values) / len(values),
        maximum=worst_value,
        worst=MeasuredWorst(row=worst_row, value=worst_value),
    )
