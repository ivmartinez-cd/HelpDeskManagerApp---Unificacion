"""Serie diaria de creados/fallidos y su pico.

Port de `_fill_daily_series` (routers/estadisticas.py): order_audit no genera filas
para días sin actividad, y sin completar con ceros el gráfico de tendencia saltearía
esos días como si no existieran en vez de mostrar un valle.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

from src.modules.insumos.domain.entities.audit_record import EVENT_CREATED, EVENT_FAILED
from src.modules.insumos.domain.value_objects.audit_statistics import DailyEventCount


@dataclass(frozen=True)
class DailyPoint:
    day: date
    created: int
    failed: int


def fill_daily_series(
    start: date, end: date, counts: Iterable[DailyEventCount]
) -> list[DailyPoint]:
    by_day: dict[date, dict[str, int]] = {}
    for row in counts:
        by_day.setdefault(row.day, {})[row.event.upper()] = row.count
    return [
        DailyPoint(
            day=day,
            created=by_day.get(day, {}).get(EVENT_CREATED, 0),
            failed=by_day.get(day, {}).get(EVENT_FAILED, 0),
        )
        for day in _days_between(start, end)
    ]


def peak_of(series: list[DailyPoint], total_created: int) -> tuple[date | None, int]:
    """(día pico, creados ese día). Sin creados en el rango no hay pico — el legacy
    devuelve None y 0 en vez del primer día de la serie con 0."""
    if total_created <= 0 or not series:
        return None, 0
    peak = max(series, key=lambda point: point.created)
    return peak.day, peak.created


def _days_between(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days
