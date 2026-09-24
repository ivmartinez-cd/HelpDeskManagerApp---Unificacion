"""Aritmética y formatos del legacy: `Math.Round` bancario sobre decimal vs.
formateo .NET de decimal (medio "lejos del cero"), cultura es-AR."""

from datetime import date
from decimal import Decimal

import pytest

from src.modules.contadores.domain.services.estimacion.formato_es_ar import (
    con_signo,
    dos_decimales,
    entero,
    fecha_corta,
    hasta_dos_decimales,
)
from src.modules.contadores.domain.services.estimacion.redondeo import a_float, redondear


@pytest.mark.parametrize(
    ("valor", "esperado"), [("2.5", 2), ("3.5", 4), ("-2.5", -2), ("2.51", 3), ("517.2413", 517)]
)
def test_redondeo_bancario(valor: str, esperado: int) -> None:
    assert a_float(redondear(Decimal(valor))) == esperado


def test_redondeo_a_dos_decimales_y_sin_menos_cero() -> None:
    assert a_float(redondear(Decimal("1.945"), 2)) == 1.94
    assert str(a_float(redondear(Decimal("-0.4")))) == "0.0"


@pytest.mark.parametrize(("valor", "esperado"), [("2.5", "3"), ("-2.5", "-3"), ("-0.4", "0")])
def test_formato_entero(valor: str, esperado: str) -> None:
    assert entero(Decimal(valor)) == esperado


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [("12.5", "12,5"), ("12", "12"), ("12.345", "12,35"), ("100.001", "100"), ("0", "0")],
)
def test_formato_hasta_dos_decimales(valor: str, esperado: str) -> None:
    assert hasta_dos_decimales(Decimal(valor)) == esperado


def test_formatos_fijos() -> None:
    assert dos_decimales(Decimal("0.5")) == "0,50"
    assert dos_decimales(Decimal("0.645161")) == "0,65"
    assert con_signo(0) == "+0"
    assert con_signo(-16) == "-16"
    assert fecha_corta(date(2026, 2, 13)) == "13/02/26"
