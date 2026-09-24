"""Cascada de parque T19 y fila pendiente (`EstimarCascadaT19` /
`ResolverCascada` / `Pendiente` del legacy)."""

from datetime import date

from src.modules.contadores.domain.services.estimacion.motor import estimar
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque


def test_resuelve_en_cliente_modelo() -> None:
    entrada = make_input(
        parque_cliente_modelo=parque(11_000),
        parque_grupo_modelo=parque(13_000),
        parque_global_modelo=parque(15_000),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Cliente_Modelo"
    assert resultado.estim_propuesto == 11_000
    assert resultado.impresiones == 11_000
    assert resultado.tipo_toma == 19
    assert resultado.requiere_confirmacion is True
    assert resultado.detalle_calculo == (
        "Sin historia propia · Parque del cliente · mismo modelo · "
        "Mediana truncada P80 · 8 equipos (0 descartados) · +11000 imp"
    )
    assert resultado.etiqueta_nivel == "Parque del cliente · mismo modelo"


def test_cae_a_grupo_modelo_sin_cliente_modelo() -> None:
    entrada = make_input(
        parque_grupo_modelo=parque(13_000),
        parque_global_modelo=parque(15_000),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Grupo_Modelo"
    assert resultado.estim_propuesto == 13_000


def test_cae_a_global_modelo_como_ultimo_recurso() -> None:
    entrada = make_input(parque_global_modelo=parque(15_000))

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Global_Modelo"
    assert resultado.estim_propuesto == 15_000


def test_nivel_con_promedio_cero_se_saltea() -> None:
    entrada = make_input(
        parque_cliente_modelo=parque(0),
        parque_global_modelo=parque(15_000),
    )

    assert estimar(entrada).fuente == "Parque_Global_Modelo"


def test_cliente_modelo_gana_a_cliente_tecnologia_aunque_historia_sea_vieja() -> None:
    entrada = make_input(
        ultimo_real=lectura(80_000, date(2025, 2, 28)),
        ultimo_contador_facturado=lectura(80_000, date(2025, 2, 28)),
        parque_cliente_modelo=parque(11_000),
        parque_cliente_tecnologia=parque(20_000, n_equipos=8),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Cliente_Modelo"
    assert resultado.estim_propuesto == 91_000


def test_cliente_tecnologia_antes_que_global_con_etiqueta_de_tecnologia() -> None:
    entrada = make_input(
        tecnologia="COLOR",
        parque_cliente_tecnologia=parque(9_000, n_equipos=3),
        parque_global_modelo=parque(15_000),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Cliente_Tec"
    assert resultado.estim_propuesto == 9_000
    assert resultado.detalle_calculo == (
        "Sin historia propia · Parque del cliente · misma tecnología (Color) · "
        "Mediana cruda · 3 equipos (muestra chica, sin truncar) · +9000 imp"
    )


def test_el_promedio_del_parque_se_redondea_al_par() -> None:
    """`BuildParqueDecision` hace `Math.Round(prom, 0)` bancario."""
    abajo = estimar(make_input(parque_cliente_modelo=parque(10_000.5)))
    arriba = estimar(make_input(parque_cliente_modelo=parque(10_001.5)))

    assert abajo.impresiones == 10_000
    assert arriba.impresiones == 10_002


def test_sin_contador_anterior_la_base_es_el_ultimo_real() -> None:
    entrada = make_input(
        ultimo_real=lectura(40_000, date(2026, 2, 15)),
        parque_cliente_modelo=parque(11_000),
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 51_000
    assert resultado.impresiones == 11_000
    assert resultado.detalle_calculo.startswith("Historia propia vieja (2m sin real) · ")


def test_detalle_parque_con_n_mayor_o_igual_a_5_es_mediana_truncada() -> None:
    entrada = make_input(
        parque_cliente_modelo=parque(
            11_000, n_equipos=14, n_descartados=2, mediana_cruda=15_000, media_cruda=18_500
        ),
    )

    resultado = estimar(entrada)

    assert resultado.detalle_parque is not None
    assert resultado.detalle_parque.es_mediana_truncada is True
    assert resultado.metodo == "MedianaTruncadaP80"
    assert resultado.marcas == frozenset()
    assert resultado.detalle_parque.n_equipos == 14
    assert resultado.detalle_parque.n_descartados == 2
    assert resultado.detalle_parque.mediana_cruda == 15_000
    assert resultado.detalle_parque.media_cruda == 18_500
    assert "Mediana truncada P80 · 14 equipos (2 descartados)" in resultado.detalle_calculo


def test_detalle_parque_con_n_menor_a_5_es_mediana_cruda() -> None:
    entrada = make_input(parque_cliente_modelo=parque(11_000, n_equipos=3))

    resultado = estimar(entrada)

    assert resultado.detalle_parque is not None
    assert resultado.detalle_parque.es_mediana_truncada is False
    assert resultado.metodo == "MedianaCruda"
    assert resultado.detalle_parque.n_descartados == 0


def test_ningun_nivel_resuelve_queda_pendiente() -> None:
    resultado = estimar(make_input(ultimo_contador_facturado=lectura(0, date(2026, 1, 1))))

    assert resultado.fuente == "Pendiente"
    assert resultado.metodo == "NoAplica"
    assert resultado.marcas == frozenset()
    assert resultado.estim_propuesto is None
    assert resultado.impresiones is None
    assert resultado.tipo_toma is None
    assert resultado.requiere_confirmacion is False
    assert resultado.semaforo == "ROJO"
    assert resultado.detalle_calculo == "Sin datos suficientes para estimar — marcar pendiente."
