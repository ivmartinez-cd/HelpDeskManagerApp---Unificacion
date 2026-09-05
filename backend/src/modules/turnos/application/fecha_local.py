"""Fecha/hora de referencia del módulo en la zona horaria de la operación.
El contenedor corre en UTC: entre las 21:00 y las 24:00 ART `date.today()`
ya es "mañana", y una grilla o asignación que vence hoy desaparecía de un
listado mientras `/current` la seguía aplicando."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

ARGENTINA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def ahora_local() -> datetime:
    return datetime.now(ARGENTINA_TZ)


def hoy_local() -> date:
    return ahora_local().date()
