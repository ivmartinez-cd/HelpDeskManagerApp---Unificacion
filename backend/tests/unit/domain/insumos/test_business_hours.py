"""Tests de business_minutes_between — los minutos hábiles del tiempo de atención."""

from datetime import UTC, datetime

from src.modules.insumos.domain.services.business_hours import business_minutes_between

WORK_START, WORK_END = 8, 18


def _at(day: int, hour: int, minute: int = 0) -> datetime:
    """2026-06-`day` a las hh:mm. El 2026-06-05 es viernes."""
    return datetime(2026, 6, day, hour, minute, tzinfo=UTC)


def test_el_fin_de_semana_no_suma_minutos() -> None:
    """Una solicitud del viernes 17hs cargada el lunes 9hs son 2 horas hábiles
    (17→18 del viernes + 8→9 del lunes), no las ~64 horas corridas."""
    minutos = business_minutes_between(_at(5, 17), _at(8, 9), WORK_START, WORK_END)

    assert minutos == 120.0


def test_solo_cuenta_lo_que_cae_dentro_de_la_ventana_laboral() -> None:
    minutos = business_minutes_between(_at(3, 6), _at(3, 9), WORK_START, WORK_END)

    assert minutos == 60.0  # de 6 a 8 nadie carga pedidos


def test_rango_invertido_o_vacio_da_cero() -> None:
    assert business_minutes_between(_at(3, 10), _at(3, 10), WORK_START, WORK_END) == 0.0
    assert business_minutes_between(_at(3, 12), _at(3, 9), WORK_START, WORK_END) == 0.0


def test_dia_completo_es_la_ventana_entera() -> None:
    minutos = business_minutes_between(_at(3, 0), _at(3, 23, 59), WORK_START, WORK_END)

    assert minutos == 600.0


def test_ventana_configurable_no_hardcodeada() -> None:
    minutos = business_minutes_between(_at(3, 0), _at(3, 23), 9, 17)

    assert minutos == 480.0
