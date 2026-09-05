"""CASOS_DE_PRUEBA.md §11 (RecalcularConPL, override manual) y §12 (reglas
de validez del par, compartidas con el cálculo automático)."""

from datetime import date

import pytest

from src.modules.contadores.domain.services.estimacion.recalcular_manual import recalcular_con_pl
from tests.unit.domain.contadores.estimacion._builders import lectura, make_ctx, make_input, receso


def test_con_receso_da_el_mismo_resultado_que_el_automatico_equivalente() -> None:
    entrada = make_input(
        ultimo_contador_facturado=lectura(0, date(2026, 4, 1)),
        recesos=[receso(date(2026, 2, 1), date(2026, 2, 28))],
    )

    resultado = recalcular_con_pl(
        make_ctx(entrada), lectura(0, date(2026, 1, 1)), lectura(6_200, date(2026, 4, 1))
    )

    assert resultado is not None
    assert resultado.estim_propuesto == pytest.approx(9_100)


def test_llegada_a_mano_es_un_t4_siempre_graba_t14() -> None:
    entrada = make_input(
        fecha_objetivo=date(2026, 6, 25),
        ultimo_contador_facturado=lectura(73_173, date(2026, 5, 19)),
    )

    resultado = recalcular_con_pl(
        make_ctx(entrada),
        lectura(64_312, date(2026, 2, 13), tipo_toma=4),
        lectura(73_173, date(2026, 5, 19), tipo_toma=4),
    )

    assert resultado is not None
    assert resultado.tipo_toma == 14
    assert resultado.fuente == "T4_ST"
    assert resultado.estim_propuesto == pytest.approx(76_624, abs=1)
    assert resultado.requiere_confirmacion is True


def test_separacion_menor_a_15_dias_descarta_la_pareja_manual() -> None:
    entrada = make_input(ultimo_contador_facturado=lectura(0, date(2026, 3, 1)))

    resultado = recalcular_con_pl(
        make_ctx(entrada), lectura(100, date(2026, 3, 1)), lectura(200, date(2026, 3, 10))
    )

    assert resultado is None


def test_llegada_menor_a_partida_descarta_la_pareja_manual() -> None:
    entrada = make_input(ultimo_contador_facturado=lectura(0, date(2026, 3, 1)))

    resultado = recalcular_con_pl(
        make_ctx(entrada), lectura(200, date(2026, 1, 1)), lectura(100, date(2026, 2, 1))
    )

    assert resultado is None
