"""Cálculo de minutos hábiles (horario laboral configurable, lunes a viernes).

Port literal de `business_hours.py` del legacy. Lo usa el tiempo de atención de
estadísticas: fuera de horario laboral nadie carga pedidos, así que una solicitud que
entra un viernes a la tarde y se carga el lunes a la mañana no debe sumar el fin de
semana entero.
"""

from datetime import date, datetime, time, timedelta


def business_minutes_between(
    start: datetime, end: datetime, work_hour_start: int, work_hour_end: int
) -> float:
    """Minutos dentro de [work_hour_start, work_hour_end) de lunes a viernes contenidos
    en [start, end]. `start` y `end` deben estar en la misma zona horaria (aware o naive,
    pero consistentes entre sí) — la función no hace conversión de TZ, eso es
    responsabilidad del caller.
    """
    if end <= start:
        return 0.0

    total = timedelta()
    day = start.date()
    last_day = end.date()
    while day <= last_day:
        if day.weekday() < 5:  # lunes(0)..viernes(4)
            total += _overlap_on(day, start, end, work_hour_start, work_hour_end)
        day += timedelta(days=1)

    return total.total_seconds() / 60.0


def _overlap_on(
    day: date, start: datetime, end: datetime, work_hour_start: int, work_hour_end: int
) -> timedelta:
    """Intersección de [start, end] con la ventana laboral de ese día."""
    window_start = datetime.combine(day, time(work_hour_start, 0), tzinfo=start.tzinfo)
    window_end = datetime.combine(day, time(work_hour_end, 0), tzinfo=start.tzinfo)
    overlap_start = max(start, window_start)
    overlap_end = min(end, window_end)
    if overlap_end <= overlap_start:
        return timedelta()
    return overlap_end - overlap_start
