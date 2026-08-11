"""Utilidades de tiempo para equipos offline.

calendar_days_offline usa tz local, outage_day usa UTC — husos distintos a propósito:
cambiar outage_day a tz local reagrupa todos los cortes y pierde la traza del evento real.
"""

from datetime import UTC, datetime, tzinfo


def calendar_days_offline(
    last_contact: datetime | None,
    now: datetime,
    tz: tzinfo | None = None,
) -> int | None:
    """Días calendario entre last_contact y now en la tz dada (o en la tz de los datetimes).

    Días calendario, no horas: un contacto a las 23:30 ART de ayer es 1 día offline hoy,
    aunque en UTC sean solo pocas horas. Devuelve None si last_contact es None.
    """
    if last_contact is None:
        return None
    if tz is not None:
        lc = last_contact.astimezone(tz)
        n = now.astimezone(tz)
    else:
        lc = last_contact
        n = now
    return (n.date() - lc.date()).days


def outage_day(last_contact: datetime) -> str:
    """Fecha UTC de la última conexión como 'YYYY-MM-DD'.

    Usada para agrupar equipos que dejaron de reportar el mismo día. Deliberadamente UTC:
    cambiar a tz local reagrupa los cortes y pierde la traza de cuándo ocurrió el evento.
    """
    return last_contact.astimezone(UTC).strftime("%Y-%m-%d")
