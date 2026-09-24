"""Salto imposible (`DetectarSaltoImposible` del legacy). Período de
facturación del builder por defecto: 30 días."""

from src.modules.contadores.domain.services.estimacion.motor import estimar
from tests.unit.domain.contadores.estimacion._builders import make_input, parque


def test_velocidad_cargada_detecta_cuando_supera_el_techo() -> None:
    entrada = make_input(velocidad_ppm=45.0, parque_cliente_modelo=parque(900_000))

    resultado = estimar(entrada)

    assert resultado.borde_salto_imposible is True
    assert resultado.semaforo == "ROJO"


def test_salto_imposible_le_gana_al_amarillo_de_cliente_tecnologia() -> None:
    entrada = make_input(velocidad_ppm=45.0, parque_cliente_tecnologia=parque(900_000))

    assert estimar(entrada).semaforo == "ROJO"


def test_sin_velocidad_cargada_asume_default_sin_falso_positivo() -> None:
    entrada = make_input(velocidad_ppm=None, parque_cliente_modelo=parque(50_000))

    assert estimar(entrada).borde_salto_imposible is False


def test_velocidad_mal_cargada_en_1_usa_default_sin_falso_positivo() -> None:
    entrada = make_input(velocidad_ppm=1.0, parque_cliente_modelo=parque(19_014))

    assert estimar(entrada).borde_salto_imposible is False


def test_velocidad_en_1_sigue_detectando_salto_realmente_imposible() -> None:
    entrada = make_input(velocidad_ppm=1.0, parque_cliente_modelo=parque(900_000))

    assert estimar(entrada).borde_salto_imposible is True
