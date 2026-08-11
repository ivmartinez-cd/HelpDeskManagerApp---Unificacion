"""Tests de los formatos de fecha exactos de Insight — port de test_timeutil.py."""

from datetime import datetime
from zoneinfo import ZoneInfo

from src.modules.insumos.domain.value_objects.insight_datetime import (
    format_arg_datetime,
    today_range_utc,
)

_BA = ZoneInfo("America/Argentina/Buenos_Aires")


def test_today_range_cubre_el_dia_local_convertido_a_utc() -> None:
    """"Hoy" en Buenos Aires (UTC-3): 00:00 local = 03:00Z, fin de día = 02:59:59Z del
    día siguiente. El string lleva Z literal, no offset +00:00."""
    reference = datetime(2026, 8, 10, 15, 30, tzinfo=_BA)

    from_date, to_date = today_range_utc("America/Argentina/Buenos_Aires", reference)

    assert from_date == "2026-08-10T03:00:00Z"
    assert to_date == "2026-08-11T02:59:59Z"


def test_today_range_cerca_de_medianoche_sigue_siendo_el_dia_local() -> None:
    """A la 1 AM local (04:00Z) el rango sigue siendo el día local completo, no el UTC."""
    reference = datetime(2026, 8, 10, 1, 0, tzinfo=_BA)

    from_date, _ = today_range_utc("America/Argentina/Buenos_Aires", reference)

    assert from_date == "2026-08-10T03:00:00Z"


def test_format_arg_datetime_convierte_utc_a_hora_argentina() -> None:
    assert format_arg_datetime("2026-08-03T14:30:00Z") == "03/08 11:30"


def test_format_arg_datetime_cruce_de_dia() -> None:
    """02:00Z es 23:00 del día anterior en Argentina."""
    assert format_arg_datetime("2026-08-04T02:00:00.000Z") == "03/08 23:00"
