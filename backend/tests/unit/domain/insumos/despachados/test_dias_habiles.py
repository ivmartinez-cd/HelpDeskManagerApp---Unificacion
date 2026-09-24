"""Tests de días hábiles: plazo de retiro en sucursal y días sin movimiento de un envío.

Calendario de referencia: el lunes 21/09/2026 arranca una semana sin feriados; el lunes
12/10/2026 es feriado (Día del Respeto a la Diversidad Cultural).
"""

from datetime import date

import pytest

from src.modules.insumos.domain.services.despachados.dias_habiles import (
    dias_habiles_transcurridos,
    es_dia_habil,
    fecha_limite_retiro,
    siguiente_dia_habil,
)

SIN_FERIADOS: frozenset[date] = frozenset()
FERIADO_12_OCT = frozenset({date(2026, 10, 12)})
FIN_DE_AÑO = frozenset({date(2026, 12, 24), date(2026, 12, 25), date(2027, 1, 1)})
PLAZO_RETIRO = 5


@pytest.mark.parametrize(
    ("dia", "esperado"),
    [
        (date(2026, 9, 21), True),  # lunes
        (date(2026, 9, 25), True),  # viernes
        (date(2026, 9, 26), False),  # sábado
        (date(2026, 9, 27), False),  # domingo
        (date(2026, 10, 12), False),  # lunes feriado
    ],
)
def test_es_dia_habil_de_lunes_a_viernes_salvo_feriado(dia: date, esperado: bool) -> None:
    assert es_dia_habil(dia, FERIADO_12_OCT) is esperado


@pytest.mark.parametrize(
    ("dia", "esperado"),
    [
        (date(2026, 9, 23), date(2026, 9, 23)),  # miércoles: el mismo día
        (date(2026, 9, 26), date(2026, 9, 28)),  # sábado -> lunes
        (date(2026, 9, 27), date(2026, 9, 28)),  # domingo -> lunes
        (date(2026, 10, 10), date(2026, 10, 13)),  # sábado + lunes feriado -> martes
    ],
)
def test_siguiente_dia_habil(dia: date, esperado: date) -> None:
    assert siguiente_dia_habil(dia, FERIADO_12_OCT) == esperado


@pytest.mark.parametrize(
    ("ingreso", "feriados", "esperado"),
    [
        pytest.param(date(2026, 9, 21), SIN_FERIADOS, date(2026, 9, 25), id="lunes"),
        pytest.param(
            date(2026, 10, 9), FERIADO_12_OCT, date(2026, 10, 16), id="viernes-antes-de-feriado"
        ),
        pytest.param(date(2026, 9, 26), SIN_FERIADOS, date(2026, 10, 2), id="sabado"),
        pytest.param(date(2026, 9, 27), SIN_FERIADOS, date(2026, 10, 2), id="domingo"),
        pytest.param(date(2026, 10, 12), FERIADO_12_OCT, date(2026, 10, 19), id="feriado"),
        pytest.param(date(2026, 12, 30), FIN_DE_AÑO, date(2027, 1, 6), id="cruza-el-año"),
        pytest.param(date(2026, 12, 24), FIN_DE_AÑO, date(2027, 1, 4), id="nochebuena"),
    ],
)
def test_fecha_limite_retiro_cuenta_el_dia_de_ingreso(
    ingreso: date, feriados: frozenset[date], esperado: date
) -> None:
    assert fecha_limite_retiro(ingreso, feriados, PLAZO_RETIRO) == esperado


def test_fecha_limite_retiro_con_otro_plazo() -> None:
    """Con 1 día hábil el límite es el propio día de ingreso (si es hábil)."""
    assert fecha_limite_retiro(date(2026, 9, 21), SIN_FERIADOS, 1) == date(2026, 9, 21)
    assert fecha_limite_retiro(date(2026, 10, 8), FERIADO_12_OCT, 3) == date(2026, 10, 13)


@pytest.mark.parametrize("plazo", [0, -3])
def test_fecha_limite_retiro_rechaza_plazos_menores_a_un_dia(plazo: int) -> None:
    with pytest.raises(ValueError, match="al menos 1 día hábil"):
        fecha_limite_retiro(date(2026, 9, 21), SIN_FERIADOS, plazo)


@pytest.mark.parametrize(
    ("desde", "hasta", "esperado"),
    [
        pytest.param(date(2026, 9, 21), date(2026, 9, 21), 0, id="mismo-dia"),
        pytest.param(date(2026, 9, 25), date(2026, 9, 21), 0, id="rango-invertido"),
        pytest.param(date(2026, 9, 21), date(2026, 9, 25), 4, id="lunes-a-viernes"),
        pytest.param(date(2026, 9, 25), date(2026, 9, 28), 1, id="viernes-a-lunes"),
        pytest.param(date(2026, 9, 26), date(2026, 9, 28), 1, id="desde-sabado"),
        pytest.param(date(2026, 9, 21), date(2026, 9, 28), 5, id="semana-completa"),
        pytest.param(date(2026, 10, 9), date(2026, 10, 12), 0, id="finde-mas-feriado"),
        pytest.param(date(2026, 10, 9), date(2026, 10, 13), 1, id="cruza-finde-y-feriado"),
        pytest.param(date(2026, 10, 7), date(2026, 10, 16), 6, id="dos-semanas-con-feriado"),
        pytest.param(date(2026, 12, 31), date(2027, 1, 4), 1, id="cruza-el-año"),
    ],
)
def test_dias_habiles_transcurridos_excluye_el_dia_inicial(
    desde: date, hasta: date, esperado: int
) -> None:
    assert dias_habiles_transcurridos(desde, hasta, FERIADO_12_OCT | FIN_DE_AÑO) == esperado
