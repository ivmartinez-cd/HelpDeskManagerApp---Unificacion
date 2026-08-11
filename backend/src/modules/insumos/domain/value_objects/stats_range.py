"""Rango de fechas de estadísticas + el período inmediatamente anterior del mismo largo.

Port de `_resolve_range` (routers/estadisticas.py). El período previo existe para las
comparativas ("creados vs. período anterior"): tiene que tener exactamente el mismo
largo que el actual y terminar el día antes de que este empiece, si no la comparación
mentiría.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from src.modules.insumos.domain.errors import RangoDeEstadisticasInvalidoError

DEFAULT_DAYS = 30


@dataclass(frozen=True)
class StatsRange:
    start: date
    end: date
    days: int
    previous_start: date
    previous_end: date


def resolve_stats_range(
    days: int | None, start_date: date | None, end_date: date | None, *, today: date
) -> StatsRange:
    """`start_date` (con `end_date` opcional, default hoy) tiene prioridad sobre `days`.
    Sin ninguno de los dos, los últimos DEFAULT_DAYS días terminando hoy."""
    start, end = _bounds(days, start_date, end_date, today=today)
    num_days = max(1, (end - start).days + 1)
    previous_end = start - timedelta(days=1)
    return StatsRange(
        start=start,
        end=end,
        days=num_days,
        previous_start=previous_end - timedelta(days=num_days - 1),
        previous_end=previous_end,
    )


def _bounds(
    days: int | None, start_date: date | None, end_date: date | None, *, today: date
) -> tuple[date, date]:
    if start_date is not None:
        end = end_date if end_date is not None else today
        if start_date > end:
            raise RangoDeEstadisticasInvalidoError(
                "start_date debe ser menor o igual a end_date"
            )
        return start_date, end
    if days is not None and days <= 0:
        raise RangoDeEstadisticasInvalidoError("days debe ser mayor a 0")
    num_days = days if days is not None else DEFAULT_DAYS
    return today - timedelta(days=num_days - 1), today
