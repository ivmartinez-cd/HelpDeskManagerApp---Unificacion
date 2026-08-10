"""Tests de normalización de series y extracción de serial de pedidos de origen interno.

Casos portados del legacy (`test_soap_query.py` + docstrings de soap_query.py), incluidos
los dos bugs reales: el punto final de Insight (falso BODEGA) y el serial que empieza con
dígito (supply 441396).
"""

import pytest

from src.modules.insumos.domain.value_objects.serial_number import (
    clean_serial,
    extract_internal_serial,
    serial_from_supply_fields,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Z83DBJEJ90000GT.", "Z83DBJEJ90000GT"),
        ("  ABC123  ", "ABC123"),
        ("ABC123\t\n", "ABC123"),
        ("ABC123", "ABC123"),
        ("", ""),
        (None, ""),
    ],
)
def test_clean_serial_strips_known_artifacts(raw: str | None, expected: str) -> None:
    assert clean_serial(raw) == expected


@pytest.mark.parametrize(
    ("nro_serie", "expected"),
    [
        # Formato A: serial al inicio, texto de porcentaje/días después.
        ("MXBCQ8Z0K6  Porcentaje: 10\nDias Restantes Est.: 3", "MXBCQ8Z0K6"),
        # Formato B: serial al final.
        ("Porcentaje: 6\nDias Restantes Est.: 10\nPHC5R19633", "PHC5R19633"),
        # Formato C: solo el serial — y puede empezar con dígito (bug real: supply 441396).
        ("0BLQBJKJ90000JV   ", "0BLQBJKJ90000JV"),
        ("", ""),
        (None, ""),
        # Los números sueltos de "Porcentaje"/"Dias Restantes" nunca deben matchear.
        ("Porcentaje: 10\nDias Restantes Est.: 3", ""),
    ],
)
def test_extract_internal_serial(nro_serie: str | None, expected: str) -> None:
    assert extract_internal_serial(nro_serie) == expected


def test_serial_from_supply_fields_prefiere_nro_serie_solicitud() -> None:
    assert serial_from_supply_fields("mxbcq8z0k6", "otro texto") == "MXBCQ8Z0K6"


def test_serial_from_supply_fields_cae_al_texto_libre_si_solicitud_vacio() -> None:
    assert serial_from_supply_fields("", "Porcentaje: 6\nPHC5R19633") == "PHC5R19633"
