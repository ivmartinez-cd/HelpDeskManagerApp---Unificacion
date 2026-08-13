"""Caracterización del dígito verificador de AyC (pesos 3-1-3-1) — los casos son
números REALES de liquidaciones de producción (DB local, validación 2026-08-13:
la fórmula reprodujo 35/35; `id % 10` solo 4/35). Los tres primeros además están
confirmados contra el SOAP en vivo (id AyC ↔ número local)."""

import pytest

from src.modules.liquidaciones.domain.services.numeracion_ayc import (
    digito_verificador,
    numero_liquidacion,
)

# (id AyC, dígito verificador real)
CASOS_REALES = [
    (3739, 6),  # PENTACOM feb-2026 — confirmado contra SOAP (getTopLiquidations)
    (3922, 4),  # JUNIN jul-2026 — confirmado contra SOAP
    (3928, 8),  # JUJUY ago-2026 — confirmado contra SOAP; coincide con id%10 de casualidad
    (3849, 2),
    (3852, 6),
    (3859, 9),
    (3874, 8),
    (3875, 7),
    (3876, 6),  # coincide con id%10 de casualidad (caso que "validó" el ADR-015)
    (3877, 5),
    (3878, 4),
    (3879, 3),
    (3881, 8),
    (3882, 7),
    (3895, 1),
    (3896, 0),
    (3904, 8),
    (3908, 4),
    (3909, 3),
    (3910, 9),
    (3911, 8),
    (3912, 7),
    (3913, 6),
    (3914, 5),
    (3915, 4),
    (3916, 3),
    (3917, 2),
    (3919, 0),
    (3920, 6),
    (3921, 5),
    (3923, 3),
    (3924, 2),
    (3925, 1),
    (3926, 0),
    (3927, 9),
]


@pytest.mark.parametrize(("liq_id", "dv"), CASOS_REALES)
def test_digito_verificador_casos_reales(liq_id: int, dv: int) -> None:
    assert digito_verificador(liq_id) == dv


@pytest.mark.parametrize(("liq_id", "dv"), CASOS_REALES)
def test_numero_liquidacion_formato(liq_id: int, dv: int) -> None:
    assert numero_liquidacion(liq_id) == f"{liq_id}-{dv}"


def test_no_es_id_modulo_10() -> None:
    """El bug original (H-1): `id % 10` NO es el dígito verificador. 3739%10=9,
    pero el número real de producción es 3739-6."""
    assert digito_verificador(3739) == 6 != 3739 % 10
