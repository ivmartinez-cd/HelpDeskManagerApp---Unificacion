"""Tests de la serie diaria de estadísticas (relleno de huecos y día pico)."""

from datetime import date

from src.modules.insumos.domain.services.statistics_series import (
    fill_daily_series,
    peak_of,
)
from src.modules.insumos.domain.value_objects.audit_statistics import DailyEventCount


def test_los_dias_sin_eventos_se_completan_con_cero() -> None:
    """order_audit no genera filas para días sin actividad: sin relleno el gráfico
    saltearía esos días en vez de mostrar el valle."""
    series = fill_daily_series(
        date(2026, 8, 1),
        date(2026, 8, 4),
        [
            DailyEventCount(day=date(2026, 8, 1), event="CREATED", count=3),
            DailyEventCount(day=date(2026, 8, 4), event="FAILED", count=1),
        ],
    )

    assert [(p.day.day, p.created, p.failed) for p in series] == [
        (1, 3, 0),
        (2, 0, 0),
        (3, 0, 0),
        (4, 0, 1),
    ]


def test_creados_y_fallidos_del_mismo_dia_van_en_el_mismo_punto() -> None:
    series = fill_daily_series(
        date(2026, 8, 1),
        date(2026, 8, 1),
        [
            DailyEventCount(day=date(2026, 8, 1), event="CREATED", count=2),
            DailyEventCount(day=date(2026, 8, 1), event="FAILED", count=5),
        ],
    )

    assert (series[0].created, series[0].failed) == (2, 5)


def test_sin_creados_no_hay_dia_pico() -> None:
    series = fill_daily_series(date(2026, 8, 1), date(2026, 8, 2), [])

    assert peak_of(series, total_created=0) == (None, 0)


def test_el_pico_es_el_dia_con_mas_creados() -> None:
    series = fill_daily_series(
        date(2026, 8, 1),
        date(2026, 8, 3),
        [
            DailyEventCount(day=date(2026, 8, 1), event="CREATED", count=2),
            DailyEventCount(day=date(2026, 8, 3), event="CREATED", count=9),
        ],
    )

    assert peak_of(series, total_created=11) == (date(2026, 8, 3), 9)
