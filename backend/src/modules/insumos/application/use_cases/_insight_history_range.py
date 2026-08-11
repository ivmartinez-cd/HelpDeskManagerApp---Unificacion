"""Rango de fechas compartido por los reads de detalle de consumible.

Insight no permite pedir históricos con más de 12 meses de antigüedad (400 Bad
Request) — 364 días para quedar del lado seguro del límite exacto (mismo criterio
que el legacy: _CONSUMABLE_HISTORY_LOOKBACK_DAYS)."""

from datetime import UTC, datetime, timedelta

LOOKBACK_DAYS = 364


def history_date_range() -> tuple[str, str]:
    """(startDate, endDate) como fechas ISO peladas — formato de consumables/history."""
    today = datetime.now(UTC).date()
    return (today - timedelta(days=LOOKBACK_DAYS)).isoformat(), today.isoformat()


def history_datetime_range() -> tuple[str, str]:
    """(fromDate, toDate) con hora y Z literal — formato de consumable-requests y
    alerts/history (el mismo string exacto que armaba el legacy)."""
    start, end = history_date_range()
    return f"{start}T00:00:00Z", f"{end}T23:59:59Z"
