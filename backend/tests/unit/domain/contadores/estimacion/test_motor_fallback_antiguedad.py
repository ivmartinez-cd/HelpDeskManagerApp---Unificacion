"""Fallback por antigüedad (`MesesSinReal` / `MesesEnAlerta` del legacy):
historia propia de más de 12 meses (mono) o 6 (color) no se usa para la
regla de tres."""

from datetime import date

from src.modules.contadores.domain.services.estimacion.antiguedad import meses_entre
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
    assert resultado.detalle_calculo == (
        "Historia propia vieja (14m sin real) · Parque del cliente · misma tecnología (Mono) · "
        "Mediana truncada P80 · 8 equipos (0 descartados) · +12000 imp"
    )


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


def test_la_alerta_se_marca_en_cualquier_rama() -> None:
    entrada = make_input(
        tecnologia="COLOR",
        ultimo_real=lectura(50_000, date(2025, 9, 30)),
        estado_maquina="EN_TRANSITO",
    )

    assert estimar(entrada).meses_sin_real_en_alerta is True


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


def test_meses_sin_real_nunca_es_negativo() -> None:
    assert meses_entre(date(2026, 6, 16), date(2026, 5, 31)) == 0
    assert meses_entre(date(2026, 3, 31), date(2026, 4, 30)) == 0
    assert meses_entre(date(2026, 3, 30), date(2026, 4, 30)) == 1
