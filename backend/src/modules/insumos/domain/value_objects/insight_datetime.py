"""Formatos de fecha exactos que exige/devuelve la Insight API — port de timeutil.py.

Es exactamente la clase de bug ya sufrido al migrar Contadores (formato exigido por HP):
replicar el string exacto, no asumir que cualquier ISO 8601 sirve.
"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

_UTC = ZoneInfo("UTC")
_ARGENTINA = ZoneInfo("America/Argentina/Buenos_Aires")


def today_range_utc(tz_name: str, reference: datetime | None = None) -> tuple[str, str]:
    """(fromDate, toDate) cubriendo "hoy" en la zona local dada, convertido a UTC en el
    formato exacto "%Y-%m-%dT%H:%M:%SZ" (Z literal, no offset +00:00) que Insight espera
    en fromDate/toDate."""
    tz = ZoneInfo(tz_name)
    now_local = (reference or datetime.now(tz)).astimezone(tz)
    start_local = datetime.combine(now_local.date(), time.min, tzinfo=tz)
    end_local = start_local + timedelta(days=1) - timedelta(milliseconds=1)
    return _to_iso(start_local.astimezone(_UTC)), _to_iso(end_local.astimezone(_UTC))


def _to_iso(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def insight_iso_to_argentina_date(raw: str | None) -> date | None:
    """Día calendario argentino de un timestamp ISO de Insight (naive = UTC) — port del
    cd_date de api_helpers, en date real en vez de string DD/MM/YYYY."""
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_UTC)
    return parsed.astimezone(_ARGENTINA).date()


def format_arg_datetime(iso_utc: str) -> str:
    """Convierte un timestamp UTC de Insight ('...Z') a hora Argentina, "dd/mm HH:MM".

    Usar SOLO con campos de Insight verificados como UTC real (`requested`/`statusDate`/
    `replacedDate` en consumable-requests, `recordDate` en consumables/history). NUNCA
    con `readDateLocal` del historial de consumibles: su convención horaria no está
    confirmada y ya causó dos conclusiones erróneas retractadas (ago-2026).
    """
    parsed = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    return parsed.astimezone(_ARGENTINA).strftime("%d/%m %H:%M")
