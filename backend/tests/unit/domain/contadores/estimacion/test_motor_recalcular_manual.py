"""`RecalcularConPL` del legacy (pareja Partida/Llegada elegida a mano)."""

from datetime import date

from src.modules.contadores.domain.services.estimacion.recalcular_manual import recalcular_con_pl
from tests.unit.domain.contadores.estimacion._builders import lectura, make_ctx, make_input, receso


def test_con_receso_da_el_mismo_resultado_que_el_automatico_equivalente() -> None:
    entrada = make_input(
        ultimo_contador_facturado=lectura(0, date(2026, 4, 1)),
        recesos=[receso(date(2026, 2, 1), date(2026, 2, 28))],
    )

    resultado = recalcular_con_pl(
        make_ctx(entrada), lectura(0, date(2026, 1, 1)), lectura(6_200, date(2026, 4, 1))
    )

    assert resultado is not None
    assert resultado.estim_propuesto == 9_100
    assert resultado.requiere_confirmacion is True
    assert resultado.marcas == {"PLManual", "AjustadoPorReceso"}
    assert resultado.detalle_calculo == (
        "P/L manual · P:01/01/26=0 · L:01/04/26=6200 · Δ62d activos (de 90d cal.) · "
        "100/día · +29d hasta fecha objetivo · receso −28d"
    )
    assert resultado.etiqueta_nivel == (
        "Pareja P/L manual · P:01/01/26=0 · L:01/04/26=6200 · ajustado por receso"
    )


def test_sin_receso_ni_t4_no_pide_confirmacion() -> None:
    entrada = make_input(ultimo_contador_facturado=lectura(1_000, date(2026, 3, 1)))

    resultado = recalcular_con_pl(
        make_ctx(entrada), lectura(1_000, date(2026, 3, 1)), lectura(4_000, date(2026, 3, 31))
    )

    assert resultado is not None
    assert resultado.estim_propuesto == 7_000
    assert resultado.impresiones == 6_000
    assert resultado.tipo_toma == 14
    assert resultado.fuente == "Historia_Propia"
    assert resultado.requiere_confirmacion is False
    assert resultado.semaforo == "VERDE"


def test_llegada_t4_graba_t14_con_fuente_t4() -> None:
    # Bug 02/07/26 del legacy: grabar T4 creaba lecturas ST ficticias en SiGes.
    entrada = make_input(
        fecha_objetivo=date(2026, 6, 25),
        ultimo_contador_facturado=lectura(73_173, date(2026, 5, 19)),
    )

    resultado = recalcular_con_pl(
        make_ctx(entrada),
        lectura(64_312, date(2026, 2, 13), tipo_toma=4),
        lectura(73_173, date(2026, 5, 19), tipo_toma=4, para_facturar=False),
    )

    assert resultado is not None
    assert resultado.tipo_toma == 14
    assert resultado.fuente == "T4_ST"
    assert resultado.metodo == "T4ST_Valor"
    assert resultado.marcas == {"PLManual", "UsaT4EnPar", "T4SinRevisar"}
    assert resultado.par_incluye_t4 is True
    assert resultado.estim_propuesto == 76_624
    assert resultado.impresiones == 3_451
    assert resultado.requiere_confirmacion is True
    assert resultado.t4_sin_revisar is True
    assert resultado.semaforo == "AMARILLO"
    assert resultado.detalle_calculo == (
        "P/L manual · P:13/02/26=64312 · L:19/05/26=73173 · Δ95d activos · 93,27/día · "
        "+37d hasta fecha objetivo"
    )


def test_llegada_posterior_a_la_fecha_objetivo_interpola_y_avisa() -> None:
    entrada = make_input(ultimo_contador_facturado=lectura(1_000, date(2026, 3, 1)))

    resultado = recalcular_con_pl(
        make_ctx(entrada), lectura(1_000, date(2026, 3, 1)), lectura(8_000, date(2026, 5, 10))
    )

    assert resultado is not None
    assert resultado.estim_propuesto == 7_000
    assert resultado.marcas == {"PLManual", "InterpoladoAtras"}
    assert resultado.detalle_calculo.endswith(
        "-10d hasta fecha objetivo · ⚠ lectura posterior a la fecha objetivo — "
        "interpolado hacia atrás"
    )


def test_pareja_sin_movimiento_es_valida() -> None:
    entrada = make_input(ultimo_contador_facturado=lectura(1_000, date(2026, 3, 1)))

    resultado = recalcular_con_pl(
        make_ctx(entrada), lectura(1_000, date(2026, 3, 1)), lectura(1_000, date(2026, 3, 31))
    )

    assert resultado is not None
    assert resultado.impresiones == 0
    assert "· 0/día ·" in resultado.detalle_calculo


def test_separacion_menor_a_15_dias_descarta_la_pareja_manual() -> None:
    entrada = make_input(ultimo_contador_facturado=lectura(0, date(2026, 3, 1)))

    resultado = recalcular_con_pl(
        make_ctx(entrada), lectura(100, date(2026, 3, 1)), lectura(200, date(2026, 3, 10))
    )

    assert resultado is None


def test_llegada_menor_a_partida_descarta_la_pareja_manual() -> None:
    entrada = make_input(ultimo_contador_facturado=lectura(0, date(2026, 3, 1)))

    resultado = recalcular_con_pl(
        make_ctx(entrada), lectura(200, date(2026, 1, 1)), lectura(100, date(2026, 2, 1))
    )

    assert resultado is None


def test_sobre_una_fila_ya_real_queda_verde_y_sin_alerta() -> None:
    # `CalcularSemaforo` devuelve Verde para toda fila no pendiente, y
    # `RecalcularConPL` conserva el `MesesSinRealEnAlerta` (false) de la fila real.
    entrada = make_input(
        pendiente_estimar=False,
        ultimo_real=lectura(1_000, date(2024, 1, 1)),
        ultimo_contador_facturado=lectura(1_000, date(2026, 3, 1)),
    )

    resultado = recalcular_con_pl(
        make_ctx(entrada), lectura(1_000, date(2026, 3, 1)), lectura(900_000, date(2026, 3, 31))
    )

    assert resultado is not None
    assert resultado.borde_salto_imposible is True
    assert resultado.semaforo == "VERDE"
    assert resultado.meses_sin_real_en_alerta is False


def test_sobre_una_fila_real_forzada_hereda_la_alerta_de_la_fila_efectiva() -> None:
    # `RecalcularConPL` hace `actual with {...}`: si la fila real ya tenía un
    # método forzado (ForzarCascada calcula MesesEnAlerta=true), el P/L lo hereda.
    entrada = make_input(
        pendiente_estimar=False,
        ultimo_real=lectura(1_000, date(2024, 1, 1)),
        ultimo_contador_facturado=lectura(1_000, date(2026, 3, 1)),
    )

    resultado = recalcular_con_pl(
        make_ctx(entrada),
        lectura(1_000, date(2026, 1, 1)),
        lectura(4_000, date(2026, 3, 1)),
        alerta_vigente=True,
    )

    assert resultado is not None
    assert resultado.semaforo == "VERDE"
    assert resultado.meses_sin_real_en_alerta is True
