"""Parseo del formato de fecha propio de Canal Directo.

"DD/MM/YYYY[ HH:MM:SS]", **ya en hora Argentina** — a diferencia de Insight, acá NO hay
`Z` ni conversión de huso que hacer (caracterización §7). Parsear explícito, nunca asumir
un CAST directo ni ISO 8601.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

CD_TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")

_CD_FORMATS = ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y")


def parse_cd_datetime(raw: str | None) -> datetime | None:
    """Devuelve un datetime aware (Buenos Aires) o None si el texto no es una fecha CD."""
    text = (raw or "").strip()
    for fmt in _CD_FORMATS:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=CD_TIMEZONE)
        except ValueError:
            continue
    return None


def format_cd_datetime(value: datetime | None) -> str:
    """Inversa de parse_cd_datetime, para vistas que muestran el formato de CD."""
    if value is None:
        return ""
    return value.astimezone(CD_TIMEZONE).strftime("%d/%m/%Y %H:%M:%S")
