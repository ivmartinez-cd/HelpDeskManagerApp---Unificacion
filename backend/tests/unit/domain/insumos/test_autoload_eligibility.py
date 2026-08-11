"""Tests del criterio compartido de elegibilidad/validación (autoload_eligibility.py)."""

from src.modules.insumos.domain.services.autoload_eligibility import (
    is_autoload_eligible,
    needs_validation,
)


def test_is_autoload_eligible_por_dias_o_por_porcentaje() -> None:
    assert is_autoload_eligible(days_left=1, percent_left=50, max_days=3, min_percent=15)
    assert is_autoload_eligible(days_left=10, percent_left=5, max_days=3, min_percent=15)
    assert not is_autoload_eligible(days_left=10, percent_left=50, max_days=3, min_percent=15)


def test_needs_validation_solo_en_cero_exacto() -> None:
    """Acotado a 0% exacto: nivel bajo pero no cero (o daysLeft corto) es una alerta
    legítima de HP SDS que no pasa por la ventana."""
    assert needs_validation(0)
    assert needs_validation(0.0)
    assert not needs_validation(5)
    assert not needs_validation(0.1)
