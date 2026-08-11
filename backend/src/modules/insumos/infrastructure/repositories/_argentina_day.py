"""El "hoy" de negocio es el día calendario argentino, no el día UTC.

Equivalente Postgres del `date(created_at, 'localtime')` del legacy, pero explícito:
`(col AT TIME ZONE 'America/Argentina/Buenos_Aires')::date` — nunca depender de la
zona horaria del servidor/contenedor (caracterización §6.2).
"""

from datetime import date, datetime

from sqlalchemy import ColumnElement, SQLColumnExpression, func

_ARGENTINA_TZ = "America/Argentina/Buenos_Aires"


def argentina_day(column: SQLColumnExpression[datetime]) -> ColumnElement[date]:
    """El día calendario argentino de un timestamptz — el "día" de las estadísticas."""
    return func.date(func.timezone(_ARGENTINA_TZ, column))


def is_today_argentina(column: SQLColumnExpression[datetime]) -> ColumnElement[bool]:
    today = func.date(func.timezone(_ARGENTINA_TZ, func.now()))
    return argentina_day(column) == today
