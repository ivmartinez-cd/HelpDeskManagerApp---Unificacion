"""Semáforo (`CalcularSemaforo` del legacy) y cálculo en lote."""

from datetime import date

import pytest

from src.modules.contadores.domain.services.estimacion.motor import estimar
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque, receso


@pytest.mark.parametrize(
    "nivel", ["parque_cliente_modelo", "parque_grupo_modelo", "parque_global_modelo"]
)
def test_parque_por_modelo_es_rojo(nivel: str) -> None:
    entrada = make_input(**{nivel: parque(11_000)})

    assert estimar(entrada).semaforo == "ROJO"


def test_parque_cliente_tecnologia_es_amarillo_no_rojo() -> None:
    resultado = estimar(make_input(parque_cliente_tecnologia=parque(11_000)))

    assert resultado.fuente == "Parque_Cliente_Tec"
    assert resultado.requiere_confirmacion is True
    assert resultado.semaforo == "AMARILLO"


def test_t4_sin_revisar_como_llegada_es_amarillo() -> None:
    entrada = make_input(
        ultimo_contador_facturado=lectura(95_000, date(2026, 3, 31)),
        t4_mas_reciente=lectura(105_000, date(2026, 4, 25), tipo_toma=4),
        t4_revisado=False,
    )

    assert estimar(entrada).semaforo == "AMARILLO"


def test_coloreo_activo_sin_otra_marca_es_naranja() -> None:
    entrada = make_input(
        ultimo_contador_facturado=lectura(95_000, date(2026, 3, 31)),
        t4_mas_reciente=lectura(105_000, date(2026, 4, 25), tipo_toma=4),
        t4_revisado=True,
        prom_6_facturados=1_000,
    )

    resultado = estimar(entrada)

    assert resultado.coloreo == "AZUL"
    assert resultado.semaforo == "NARANJA"


def test_entre_dos_reales_sin_marcas_es_verde() -> None:
    entrada = make_input(
        real_anterior=lectura(100_000, date(2026, 2, 1)),
        ultimo_real=lectura(130_000, date(2026, 3, 31)),
        ultimo_contador_facturado=lectura(120_000, date(2026, 3, 31)),
    )

    assert estimar(entrada).semaforo == "VERDE"


def test_un_lote_devuelve_un_resultado_por_equipo_sin_excepciones() -> None:
    entradas = [
        make_input(pendiente_estimar=False),
        make_input(parque_cliente_modelo=parque(11_000)),
        make_input(
            real_anterior=lectura(0, date(2026, 1, 1)),
            ultimo_real=lectura(6_200, date(2026, 4, 1)),
            ultimo_contador_facturado=lectura(0, date(2026, 4, 1)),
            recesos=[receso(date(2026, 2, 1), date(2026, 2, 28))],
        ),
        make_input(estado_maquina="EN_TRANSITO"),
    ]

    resultados = [estimar(e) for e in entradas]

    assert len(resultados) == len(entradas)
