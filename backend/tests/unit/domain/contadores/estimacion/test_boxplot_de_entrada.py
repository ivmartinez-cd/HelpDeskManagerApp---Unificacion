"""`CalcularBoxplotData` de `PanelCandidatos` (legacy)."""

from datetime import date

from src.modules.contadores.application.use_cases._boxplot_de_entrada import boxplot_de_entrada
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque


def test_usa_el_parque_por_tecnologia_con_sus_cuartiles() -> None:
    entrada = make_input(
        parque_cliente_tecnologia=parque(9_000, n_equipos=12, q1=6_000, q3=11_000),
        parque_cliente_modelo=parque(20_000),
    )

    boxplot = boxplot_de_entrada(entrada)

    assert boxplot is not None
    assert boxplot.mediana == 9_000
    assert (boxplot.q1, boxplot.q3, boxplot.n_equipos) == (6_000, 11_000, 12)
    assert boxplot.valor_equipo == 20_000


def test_sin_parque_por_tecnologia_usa_el_de_modelo_sin_cuartiles() -> None:
    entrada = make_input(
        ultimo_contador_facturado=lectura(0, date(2026, 3, 31)),
        parque_cliente_modelo=parque(20_000),
    )

    boxplot = boxplot_de_entrada(entrada)

    assert boxplot is not None
    assert boxplot.mediana == 20_000
    assert (boxplot.q1, boxplot.q3, boxplot.n_equipos) == (None, None, 0)


def test_sin_parque_del_cliente_no_hay_grafico() -> None:
    entrada = make_input(parque_global_modelo=parque(20_000))

    assert boxplot_de_entrada(entrada) is None


def test_con_las_impresiones_de_la_fila_las_usa_en_vez_de_la_propuesta() -> None:
    # `Equipo.Impresiones` del legacy: la fila con la decisión del operador aplicada.
    entrada = make_input(
        parque_cliente_tecnologia=parque(9_000), parque_cliente_modelo=parque(20_000)
    )

    boxplot = boxplot_de_entrada(entrada, impresiones_fila=7_500)

    assert boxplot is not None
    assert boxplot.valor_equipo == 7_500
