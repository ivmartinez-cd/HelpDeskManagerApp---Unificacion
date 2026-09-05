"""CASOS_DE_PRUEBA.md §1 (lectura real existente) y §2 (entre dos reales)."""

from datetime import date

from src.modules.contadores.domain.services.estimacion.motor import estimar
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque


def test_lectura_real_no_propone_estimado() -> None:
    entrada = make_input(pendiente_estimar=False)

    resultado = estimar(entrada)

    assert resultado.estim_propuesto is None
    assert resultado.semaforo == "VERDE"
    assert resultado.fuente == "Sin_Estimar"


def test_entre_dos_reales_calculo_basico() -> None:
    entrada = make_input(
        real_anterior=lectura(100_000, date(2026, 2, 1)),
        ultimo_real=lectura(130_000, date(2026, 3, 31)),
        ultimo_contador_facturado=lectura(120_000, date(2026, 3, 31)),
    )

    resultado = estimar(entrada)

    assert 145_000 <= resultado.estim_propuesto <= 146_000  # type: ignore[operator]
    assert resultado.tipo_toma == 14
    assert resultado.fuente == "Historia_Propia"
    assert resultado.requiere_confirmacion is False


def test_entre_dos_reales_interpola_hacia_atras() -> None:
    entrada = make_input(
        fecha_objetivo=date(2026, 5, 31),
        real_anterior=lectura(26_579, date(2026, 3, 17)),
        ultimo_real=lectura(43_226, date(2026, 6, 16)),
        ultimo_contador_facturado=lectura(30_884, date(2026, 5, 1)),
    )

    resultado = estimar(entrada)

    assert 40_000 <= resultado.estim_propuesto <= 40_600  # type: ignore[operator]
    assert resultado.estim_propuesto < 43_226
    assert 9_200 <= resultado.impresiones <= 9_600  # type: ignore[operator]
    assert resultado.fuente == "Historia_Propia"


def test_separacion_menor_a_15_dias_descarta_el_par() -> None:
    entrada = make_input(
        real_anterior=lectura(125_000, date(2026, 3, 21)),
        ultimo_real=lectura(130_000, date(2026, 3, 31)),
        parque_cliente_tecnologia=parque(10_000, n_equipos=8),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Cliente_Tec"
    assert resultado.tipo_toma == 19
