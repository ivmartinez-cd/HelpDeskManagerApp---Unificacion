"""Mismos valores capturados en vivo contra la app vieja (POST /api/tools/calc)
el 2026-08-07 — ver CONTADORES_CARACTERIZACION.md."""

from datetime import date

import pytest

from src.modules.contadores.domain.errors import InvalidDateRangeError
from src.modules.contadores.domain.services.manual_estimation_calculator import (
    calculate_manual_estimation,
)
from src.modules.contadores.domain.value_objects.manual_estimation_input import (
    ManualEstimationInput,
)


def test_matches_legacy_response_including_negative_dias_est_when_fe_precedes_ff() -> None:
    # fe (15/01) es anterior a ff (01/02): dias_360 "hacia atras" da negativo,
    # es matematicamente correcto para ese orden, no un caso a corregir.
    data = ManualEstimationInput(
        contador_inicial=1000,
        contador_final=2000,
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 2, 1),
        fecha_estimacion=date(2026, 1, 15),
    )

    result = calculate_manual_estimation(data)

    assert result.imp_dia == 33.33
    assert result.imp_mes == 999.9
    assert result.dias_est == -16
    assert result.imp_est == -533
    assert result.cont_est == 1467


def test_forward_estimation_gives_positive_days_and_counter() -> None:
    data = ManualEstimationInput(
        contador_inicial=1000,
        contador_final=2000,
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 2, 1),
        fecha_estimacion=date(2026, 3, 1),
    )

    result = calculate_manual_estimation(data)

    assert result.dias_est == 30
    assert result.imp_est == 1000
    assert result.cont_est == 3000


def test_zero_or_negative_range_between_fi_and_ff_is_rejected() -> None:
    data = ManualEstimationInput(
        contador_inicial=1000,
        contador_final=2000,
        fecha_inicial=date(2026, 2, 1),
        fecha_final=date(2026, 1, 1),
        fecha_estimacion=date(2026, 3, 1),
    )

    with pytest.raises(InvalidDateRangeError):
        calculate_manual_estimation(data)
