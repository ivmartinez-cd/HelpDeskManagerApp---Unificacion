"""Coloreo bidireccional (`CalcularColoreo` del legacy): contra el promedio de
los últimos 6 procesos facturados, factores 1,4 / 0,6."""

from src.modules.contadores.domain.services.estimacion.motor import estimar
from tests.unit.domain.contadores.estimacion._builders import make_input, parque


def test_azul_cuando_supera_1_4_veces_el_promedio() -> None:
    entrada = make_input(parque_cliente_modelo=parque(20_000), prom_6_facturados=10_000)

    assert estimar(entrada).coloreo == "AZUL"


def test_naranja_cuando_es_menor_a_0_6_veces_el_promedio() -> None:
    entrada = make_input(parque_cliente_modelo=parque(5_000), prom_6_facturados=10_000)

    assert estimar(entrada).coloreo == "NARANJA"


def test_normal_dentro_del_rango() -> None:
    entrada = make_input(parque_cliente_modelo=parque(10_000), prom_6_facturados=10_000)

    assert estimar(entrada).coloreo == "NORMAL"


def test_justo_en_el_limite_no_colorea() -> None:
    entrada = make_input(parque_cliente_modelo=parque(14_000), prom_6_facturados=10_000)

    assert estimar(entrada).coloreo == "NORMAL"


def test_sin_promedio_de_referencia_es_normal() -> None:
    entrada = make_input(parque_cliente_modelo=parque(20_000), prom_6_facturados=None)

    assert estimar(entrada).coloreo == "NORMAL"


def test_equipo_sin_movimiento_no_se_colorea() -> None:
    entrada = make_input(estado_maquina="EN_TRANSITO", prom_6_facturados=10_000)

    assert estimar(entrada).coloreo == "NORMAL"
