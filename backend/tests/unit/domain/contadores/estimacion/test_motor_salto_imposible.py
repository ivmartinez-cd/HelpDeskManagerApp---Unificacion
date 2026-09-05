"""CASOS_DE_PRUEBA.md §7 — salto imposible (REGLAS_DE_NEGOCIO §7.1).
Período de facturación del builder por defecto: 30 días."""

from datetime import date

from src.modules.contadores.domain.services.estimacion.motor import estimar
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque

_SIN_FACTURADO = lectura(0, date(2026, 3, 1))


def test_velocidad_cargada_detecta_cuando_supera_el_techo() -> None:
    entrada = make_input(
        tecnologia="MONO",
        velocidad_ppm=45.0,
        ultimo_contador_facturado=_SIN_FACTURADO,
        parque_cliente_modelo=parque(900_000),
    )

    resultado = estimar(entrada)

    assert resultado.borde_salto_imposible is True
    assert resultado.semaforo == "ROJO"


def test_sin_velocidad_cargada_asume_default_sin_falso_positivo() -> None:
    entrada = make_input(
        tecnologia="MONO",
        velocidad_ppm=None,
        ultimo_contador_facturado=_SIN_FACTURADO,
        parque_cliente_modelo=parque(50_000),
    )

    resultado = estimar(entrada)

    assert resultado.borde_salto_imposible is False


def test_velocidad_mal_cargada_en_1_usa_default_sin_falso_positivo() -> None:
    entrada = make_input(
        tecnologia="MONO",
        velocidad_ppm=1.0,
        ultimo_contador_facturado=_SIN_FACTURADO,
        parque_cliente_modelo=parque(19_014),
    )

    resultado = estimar(entrada)

    assert resultado.borde_salto_imposible is False


def test_velocidad_en_1_sigue_detectando_salto_realmente_imposible() -> None:
    entrada = make_input(
        tecnologia="MONO",
        velocidad_ppm=1.0,
        ultimo_contador_facturado=_SIN_FACTURADO,
        parque_cliente_modelo=parque(900_000),
    )

    resultado = estimar(entrada)

    assert resultado.borde_salto_imposible is True
