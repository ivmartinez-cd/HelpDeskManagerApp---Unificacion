"""Tests de calendar_days_offline y outage_day."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from src.modules.insumos.domain.value_objects.offline_clock import (
    calendar_days_offline,
    outage_day,
)

_ART = ZoneInfo("America/Argentina/Buenos_Aires")  # UTC-3, sin DST


def _art(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=_ART)


def _utc(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


# ------ calendar_days_offline ------


def test_contacto_ayer_23_30_art_es_1_dia_offline() -> None:
    """Ayer 23:30 ART = hoy 02:30 UTC. En UTC serían 0 días, en ART son 1. Correcto: 1."""
    last_contact = _art(2026, 8, 10, 23, 30)
    now = _art(2026, 8, 11, 10, 0)
    assert calendar_days_offline(last_contact, now, tz=_ART) == 1


def test_contacto_mismo_dia_es_0_dias() -> None:
    last_contact = _art(2026, 8, 11, 8, 0)
    now = _art(2026, 8, 11, 18, 0)
    assert calendar_days_offline(last_contact, now, tz=_ART) == 0


def test_contacto_tres_dias_atras() -> None:
    last_contact = _art(2026, 8, 8, 12, 0)
    now = _art(2026, 8, 11, 12, 0)
    assert calendar_days_offline(last_contact, now, tz=_ART) == 3


def test_none_devuelve_none() -> None:
    assert calendar_days_offline(None, _art(2026, 8, 11, 12, 0)) is None


def test_sin_tz_usa_los_dates_tal_cual() -> None:
    """Sin tz, usa date() de los datetimes directamente."""
    lc = _utc(2026, 8, 10, 23, 30)
    now = _utc(2026, 8, 11, 2, 0)
    # En UTC ambos son distintos días → 1
    assert calendar_days_offline(lc, now) == 1


# ------ outage_day ------


def test_outage_day_usa_utc() -> None:
    """23:30 ART = 02:30 UTC del día siguiente → outage_day devuelve el día UTC."""
    lc = _art(2026, 8, 10, 23, 30)  # = 2026-08-11 02:30 UTC
    assert outage_day(lc) == "2026-08-11"


def test_outage_day_mediodia_utc() -> None:
    lc = _utc(2026, 8, 10, 12, 0)
    assert outage_day(lc) == "2026-08-10"


@pytest.mark.parametrize("offset_hours", [3, -3, 0])
def test_outage_day_normaliza_a_utc_sin_importar_tz_input(offset_hours: int) -> None:
    """El día siempre se calcula en UTC, sin importar la tz del datetime recibido."""
    from datetime import timedelta, timezone

    tz = timezone(timedelta(hours=offset_hours))
    # 2026-08-11 12:00 en cualquier tz → en UTC puede ser otro día solo si el offset cambia la fecha
    lc = datetime(2026, 8, 11, 12, 0, tzinfo=tz)
    day = outage_day(lc)
    expected = lc.astimezone(UTC).strftime("%Y-%m-%d")
    assert day == expected
