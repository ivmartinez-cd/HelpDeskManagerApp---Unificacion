"""CASOS_DE_PRUEBA.md §4 — cascada de parque T19 sin historia propia
(REGLAS_DE_NEGOCIO §5.5)."""

from datetime import date

from src.modules.contadores.domain.services.estimacion.motor import estimar
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque

_SIN_FACTURADO = lectura(0, date(2026, 1, 1))


def test_resuelve_en_cliente_modelo() -> None:
    entrada = make_input(
        ultimo_contador_facturado=_SIN_FACTURADO,
        parque_cliente_modelo=parque(11_000),
        parque_grupo_modelo=parque(13_000),
        parque_global_modelo=parque(15_000),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Cliente_Modelo"
    assert resultado.estim_propuesto == 11_000
    assert resultado.tipo_toma == 19
    assert resultado.requiere_confirmacion is True
    assert resultado.semaforo == "ROJO"


def test_cae_a_grupo_modelo_sin_cliente_modelo() -> None:
    entrada = make_input(
        ultimo_contador_facturado=_SIN_FACTURADO,
        parque_grupo_modelo=parque(13_000),
        parque_global_modelo=parque(15_000),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Grupo_Modelo"
    assert resultado.estim_propuesto == 13_000


def test_cae_a_global_modelo_como_ultimo_recurso() -> None:
    entrada = make_input(
        ultimo_contador_facturado=_SIN_FACTURADO,
        parque_global_modelo=parque(15_000),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Global_Modelo"
    assert resultado.estim_propuesto == 15_000


def test_cliente_modelo_gana_a_cliente_tecnologia_aunque_historia_sea_vieja() -> None:
    entrada = make_input(
        ultimo_contador_facturado=_SIN_FACTURADO,
        ultimo_real=lectura(80_000, date(2025, 2, 28)),
        parque_cliente_modelo=parque(11_000),
        parque_cliente_tecnologia=parque(20_000, n_equipos=8),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Cliente_Modelo"
    assert resultado.estim_propuesto == 11_000


def test_cliente_tecnologia_antes_que_global() -> None:
    entrada = make_input(
        ultimo_contador_facturado=_SIN_FACTURADO,
        parque_cliente_tecnologia=parque(9_000, n_equipos=8),
        parque_global_modelo=parque(15_000),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Cliente_Tec"
    assert resultado.estim_propuesto == 9_000


def test_ningun_nivel_resuelve_queda_pendiente() -> None:
    entrada = make_input(ultimo_contador_facturado=_SIN_FACTURADO)

    resultado = estimar(entrada)

    assert resultado.fuente == "Pendiente"
    assert resultado.estim_propuesto is None
    assert resultado.semaforo == "ROJO"
