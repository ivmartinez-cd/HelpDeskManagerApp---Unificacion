"""Tests de normalize_company_name, expand_alias y same_company."""

import pytest

from src.modules.insumos.domain.services.company_matching import (
    expand_alias,
    normalize_company_name,
    same_company,
)


def test_normaliza_acentos_y_mayusculas() -> None:
    # "S.A." con puntos: las letras quedan como tokens separados ("s a"), no se eliminan
    # porque el regex busca "sa" como token único. same_company lo maneja por contención.
    assert normalize_company_name("Héctor García SA") == "hector garcia"


def test_elimina_razon_social_sin_puntos() -> None:
    assert normalize_company_name("ARCOR SAIC") == "arcor"


def test_colapsa_espacios() -> None:
    assert normalize_company_name("  Empresa   SRL  ") == "empresa"


def test_sufijo_con_puntos_no_se_elimina_solo_la_puntuacion() -> None:
    """'S.A.' queda como 's a' tras quitar puntos — same_company lo resuelve por contención."""
    assert normalize_company_name("Empresa S.A.") == "empresa s a"


def test_alias_palabra_exacta() -> None:
    """ausol matchea como token exacto, no como substring de otra palabra."""
    assert expand_alias("ausol") == "autopistas del sol"
    assert expand_alias("causolar") == "causolar"  # no matchea


def test_alias_multipalabra_como_substring() -> None:
    assert expand_alias("concesionario del oeste autopistas") == "autopistas del sol autopistas"


def test_gco_sin_grupo_porque_legal_suffix_lo_saca() -> None:
    """'grupo' sale por _LEGAL_SUFFIX_RE antes de que _expand_alias vea el string."""
    assert same_company("Grupo Concesionario del Oeste", "Autopistas del Sol")


def test_contencion_bidireccional() -> None:
    """'Cartocor /Arcor' contiene 'arcor' tras normalizar → mismo cliente."""
    assert same_company("Cartocor /Arcor", "ARCOR SAIC")
    assert same_company("ARCOR SAIC", "Cartocor /Arcor")


def test_meli_token_exacto() -> None:
    assert same_company("Meli", "Mercado Libre")
    assert not same_company("Amelio SRL", "Mercado Libre")


def test_arcadium_alias_multipalabra() -> None:
    assert same_company("Sal de Vida S.A.", "Arcadium Lithium")
    assert same_company("Minera del Altiplano", "Arcadium Lithium")
    assert same_company("Sales de Jujuy", "Arcadium Lithium")


def test_nombre_vacio_devuelve_false() -> None:
    assert not same_company("", "Empresa")
    assert not same_company("Empresa", "")


def test_mismo_nombre_es_mismo_cliente() -> None:
    assert same_company("Givaudan Argentina", "Givaudan Argentina")


def test_nombres_distintos_no_son_mismo_cliente() -> None:
    assert not same_company("Empresa Alfa", "Empresa Beta")


@pytest.mark.parametrize(
    "a, b",
    [
        ("PSM", "Enap Sipetrol YPF"),
        ("Enap Sipetrol YPF", "PSM"),
    ],
)
def test_psm_enap_alias(a: str, b: str) -> None:
    assert same_company(a, b)
