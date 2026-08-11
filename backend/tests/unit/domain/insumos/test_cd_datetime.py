"""Tests del parseo del formato de fecha propio de Canal Directo (hora Argentina)."""

from datetime import datetime

from src.modules.insumos.domain.value_objects.cd_datetime import (
    CD_TIMEZONE,
    format_cd_datetime,
    parse_cd_datetime,
)


def test_parse_fecha_con_hora() -> None:
    parsed = parse_cd_datetime("31/07/2026 10:00:00")
    assert parsed == datetime(2026, 7, 31, 10, 0, 0, tzinfo=CD_TIMEZONE)


def test_parse_fecha_sin_hora() -> None:
    parsed = parse_cd_datetime("30/07/2026")
    assert parsed == datetime(2026, 7, 30, tzinfo=CD_TIMEZONE)


def test_parse_texto_invalido_devuelve_none() -> None:
    assert parse_cd_datetime("x") is None
    assert parse_cd_datetime("") is None
    assert parse_cd_datetime(None) is None
    # ISO de Insight NO es formato CD — no debe parsear en silencio como otra cosa.
    assert parse_cd_datetime("2026-07-31T10:00:00.000Z") is None


def test_format_es_la_inversa_del_parse() -> None:
    assert format_cd_datetime(parse_cd_datetime("31/07/2026 10:00:00")) == "31/07/2026 10:00:00"
    assert format_cd_datetime(None) == ""
