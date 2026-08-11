"""Tests de resolve_stats_range — el rango pedido y su período comparativo."""

from datetime import date

import pytest

from src.modules.insumos.domain.errors import RangoDeEstadisticasInvalidoError
from src.modules.insumos.domain.value_objects.stats_range import resolve_stats_range

HOY = date(2026, 8, 11)


def test_sin_parametros_son_los_ultimos_30_dias_terminando_hoy() -> None:
    period = resolve_stats_range(None, None, None, today=HOY)

    assert (period.start, period.end, period.days) == (date(2026, 7, 13), HOY, 30)


def test_el_periodo_previo_tiene_el_mismo_largo_y_termina_el_dia_anterior() -> None:
    """Si no fueran del mismo largo la comparativa "vs. período anterior" mentiría."""
    period = resolve_stats_range(7, None, None, today=HOY)

    assert (period.start, period.end) == (date(2026, 8, 5), HOY)
    assert (period.previous_start, period.previous_end) == (
        date(2026, 7, 29),
        date(2026, 8, 4),
    )
    assert (period.previous_end - period.previous_start).days == (
        period.end - period.start
    ).days


def test_start_date_tiene_prioridad_sobre_days() -> None:
    period = resolve_stats_range(7, date(2026, 1, 1), date(2026, 1, 10), today=HOY)

    assert (period.start, period.end, period.days) == (
        date(2026, 1, 1),
        date(2026, 1, 10),
        10,
    )


def test_start_date_sin_end_date_llega_hasta_hoy() -> None:
    period = resolve_stats_range(None, date(2026, 8, 9), None, today=HOY)

    assert (period.start, period.end, period.days) == (date(2026, 8, 9), HOY, 3)


def test_rango_invertido_es_invalido() -> None:
    with pytest.raises(RangoDeEstadisticasInvalidoError):
        resolve_stats_range(None, date(2026, 8, 11), date(2026, 8, 1), today=HOY)


def test_days_no_positivo_es_invalido() -> None:
    with pytest.raises(RangoDeEstadisticasInvalidoError):
        resolve_stats_range(0, None, None, today=HOY)


def test_un_solo_dia_cuenta_como_un_dia_no_como_cero() -> None:
    period = resolve_stats_range(None, HOY, HOY, today=HOY)

    assert period.days == 1
    assert period.previous_start == period.previous_end == date(2026, 8, 10)
