"""CASOS_DE_PRUEBA.md §3 — fallback por antigüedad (REGLAS_DE_NEGOCIO §5.4)."""

from datetime import date

from src.modules.contadores.domain.services.estimacion.motor import estimar
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque


def test_mono_mas_de_12_meses_cae_a_parque() -> None:
    entrada = make_input(
        tecnologia="MONO",
        ultimo_real=lectura(80_000, date(2025, 2, 28)),
        ultimo_contador_facturado=lectura(80_000, date(2025, 2, 28)),
        parque_cliente_tecnologia=parque(12_000, n_equipos=8),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Cliente_Tec"
    assert resultado.tipo_toma == 19
    assert resultado.meses_sin_real_en_alerta is True
    assert resultado.estim_propuesto == 92_000


def test_color_mas_de_6_meses_cae_a_parque() -> None:
    entrada = make_input(
        tecnologia="COLOR",
        ultimo_real=lectura(50_000, date(2025, 9, 30)),
        ultimo_contador_facturado=lectura(50_000, date(2025, 9, 30)),
        parque_cliente_tecnologia=parque(8_000, n_equipos=8),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Cliente_Tec"
    assert resultado.meses_sin_real_en_alerta is True


def test_muestra_chica_sin_iqr_no_falla() -> None:
    entrada = make_input(
        tecnologia="MONO",
        ultimo_real=lectura(5_000, date(2024, 11, 30)),
        ultimo_contador_facturado=lectura(5_000, date(2024, 11, 30)),
        parque_cliente_tecnologia=parque(9_500, n_equipos=3, q1=None, q3=None),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Cliente_Tec"
    assert resultado.estim_propuesto == 5_000 + 9_500


def test_limite_exacto_de_12_meses_no_dispara_alerta() -> None:
    entrada = make_input(
        tecnologia="MONO",
        real_anterior=lectura(50_000, date(2025, 4, 1)),
        ultimo_real=lectura(60_000, date(2025, 4, 30)),
        ultimo_contador_facturado=lectura(60_000, date(2025, 4, 30)),
    )

    resultado = estimar(entrada)

    assert resultado.meses_sin_real_en_alerta is False
    assert resultado.fuente == "Historia_Propia"
