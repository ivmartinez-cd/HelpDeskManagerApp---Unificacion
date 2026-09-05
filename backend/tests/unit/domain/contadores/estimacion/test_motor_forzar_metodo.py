from datetime import date

import pytest

from src.modules.contadores.domain.services.estimacion.forzar_metodo import (
    forzar_cascada_parque,
    forzar_entre_reales,
)
from tests.unit.domain.contadores.estimacion._builders import (
    lectura,
    make_ctx,
    make_input,
    parque,
    receso,
)


def test_forzar_entre_reales_con_par_valido_da_lo_mismo_que_el_automatico() -> None:
    """Mismo escenario que el Caso A de recesos (§5/§11 CASOS_DE_PRUEBA) —
    forzar debe dar el mismo 9.100 que el cálculo automático equivalente."""
    entrada = make_input(
        real_anterior=lectura(0, date(2026, 1, 1)),
        ultimo_real=lectura(6_200, date(2026, 4, 1)),
        ultimo_contador_facturado=lectura(0, date(2026, 4, 1)),
        recesos=[receso(date(2026, 2, 1), date(2026, 2, 28))],
    )

    resultado = forzar_entre_reales(make_ctx(entrada))

    assert resultado is not None
    assert resultado.estim_propuesto == pytest.approx(9_100)


def test_forzar_entre_reales_ignora_historia_en_alerta() -> None:
    """A diferencia del cálculo automático (que cae a parque si la historia
    es "vieja", §5.4), forzar entre reales igual corre la regla de tres si
    el par en sí es válido — el operador decidió confiar en este par."""
    entrada = make_input(
        fecha_objetivo=date(2026, 4, 30),
        real_anterior=lectura(100_000, date(2024, 1, 1)),
        ultimo_real=lectura(130_000, date(2024, 3, 1)),  # > 12 meses de antigüedad
        ultimo_contador_facturado=lectura(120_000, date(2024, 3, 1)),
        parque_cliente_tecnologia=parque(10_000),
    )

    resultado = forzar_entre_reales(make_ctx(entrada))

    assert resultado is not None
    assert resultado.fuente == "Historia_Propia"


def test_forzar_entre_reales_sin_par_valido_da_none() -> None:
    entrada = make_input(ultimo_real=None, real_anterior=None)

    assert forzar_entre_reales(make_ctx(entrada)) is None


def test_forzar_entre_reales_separacion_menor_a_15_dias_da_none() -> None:
    entrada = make_input(
        real_anterior=lectura(125_000, date(2026, 3, 21)),
        ultimo_real=lectura(130_000, date(2026, 3, 31)),
    )

    assert forzar_entre_reales(make_ctx(entrada)) is None


def test_forzar_cascada_parque_ignora_que_habia_un_par_de_reales_mejor() -> None:
    """A diferencia del cálculo automático (que preferiría "entre dos
    reales" si hay un par válido, §5.2 antes que §5.5), forzar cascada de
    parque siempre usa el parque."""
    entrada = make_input(
        real_anterior=lectura(100_000, date(2026, 2, 1)),
        ultimo_real=lectura(130_000, date(2026, 3, 31)),
        ultimo_contador_facturado=lectura(120_000, date(2026, 3, 31)),
        parque_cliente_modelo=parque(11_000),
    )

    resultado = forzar_cascada_parque(make_ctx(entrada))

    assert resultado is not None
    assert resultado.fuente == "Parque_Cliente_Modelo"
    assert resultado.estim_propuesto == pytest.approx(120_000 + 11_000)
    assert resultado.tipo_toma == 19
    assert resultado.requiere_confirmacion is True


def test_forzar_cascada_parque_sin_ningun_nivel_da_none() -> None:
    entrada = make_input()

    assert forzar_cascada_parque(make_ctx(entrada)) is None
