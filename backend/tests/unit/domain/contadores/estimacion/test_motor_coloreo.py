"""CASOS_DE_PRUEBA.md §8 — coloreo bidireccional (REGLAS_DE_NEGOCIO §7.2)."""

from datetime import date

from src.modules.contadores.domain.services.estimacion.motor import estimar
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque

_SIN_FACTURADO = lectura(0, date(2026, 3, 1))


def test_azul_cuando_supera_1_4_veces_el_promedio() -> None:
    entrada = make_input(
        ultimo_contador_facturado=_SIN_FACTURADO,
        parque_cliente_modelo=parque(20_000),
        prom_6_facturados=10_000,
    )

    assert estimar(entrada).coloreo == "AZUL"


def test_naranja_cuando_es_menor_a_0_6_veces_el_promedio() -> None:
    entrada = make_input(
        ultimo_contador_facturado=_SIN_FACTURADO,
        parque_cliente_modelo=parque(5_000),
        prom_6_facturados=10_000,
    )

    assert estimar(entrada).coloreo == "NARANJA"


def test_normal_dentro_del_rango() -> None:
    entrada = make_input(
        ultimo_contador_facturado=_SIN_FACTURADO,
        parque_cliente_modelo=parque(10_000),
        prom_6_facturados=10_000,
    )

    assert estimar(entrada).coloreo == "NORMAL"
