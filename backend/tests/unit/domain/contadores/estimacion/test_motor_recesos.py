"""Ajuste por recesos del cliente (`DiasActivos`, `DiasActivosProyeccion`,
`FactorActivoPeriodo` y `Receso.AplicaA` del legacy)."""

from datetime import date

from src.modules.contadores.domain.services.estimacion.motor import estimar
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque, receso

_PAR_CON_FEBRERO = dict(
    real_anterior=lectura(0, date(2026, 1, 1)),
    ultimo_real=lectura(6_200, date(2026, 4, 1)),
    ultimo_contador_facturado=lectura(0, date(2026, 4, 1)),
)


def test_receso_entre_los_reales_no_diluye_la_tasa() -> None:
    entrada = make_input(**_PAR_CON_FEBRERO, recesos=[receso(date(2026, 2, 1), date(2026, 2, 28))])

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 9_100
    assert resultado.requiere_confirmacion is True
    assert resultado.semaforo == "AMARILLO"
    assert resultado.dias_receso_descontados == 28
    assert resultado.detalle_calculo == (
        "Entre dos reales · Δ62d activos (de 90d cal.) · 100/día · +29d a fecha objetivo · "
        "Llegada 9100 · receso −28d"
    )
    assert resultado.etiqueta_nivel == (
        "Entre dos lecturas reales del propio equipo · ajustado por receso"
    )


def test_recesos_superpuestos_cuentan_cada_dia_una_sola_vez() -> None:
    entrada = make_input(
        **_PAR_CON_FEBRERO,
        recesos=[
            receso(date(2026, 2, 1), date(2026, 2, 20)),
            receso(date(2026, 2, 10), date(2026, 2, 28)),
        ],
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 9_100
    assert resultado.dias_receso_descontados == 28


def test_receso_en_ventana_de_proyeccion_no_factura_el_receso() -> None:
    entrada = make_input(
        fecha_objetivo=date(2026, 1, 31),
        real_anterior=lectura(0, date(2025, 11, 1)),
        ultimo_real=lectura(6_000, date(2025, 12, 1)),
        ultimo_contador_facturado=lectura(0, date(2025, 12, 1)),
        recesos=[receso(date(2025, 12, 15), date(2026, 1, 15))],
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 11_800
    assert resultado.detalle_calculo == (
        "Entre dos reales · Δ30d activos (de 30d cal.) · 200/día · +29d a fecha objetivo · "
        "Llegada 11800 · receso −32d"
    )


def test_interpolacion_hacia_atras_tambien_descuenta_recesos() -> None:
    entrada = make_input(
        real_anterior=lectura(0, date(2026, 1, 30)),
        ultimo_real=lectura(12_000, date(2026, 5, 30)),
        recesos=[receso(date(2026, 5, 10), date(2026, 5, 19))],
    )

    resultado = estimar(entrada)

    assert resultado.dias_proyectados == -20
    assert resultado.estim_propuesto == 9_818
    assert resultado.detalle_calculo == (
        "Entre dos reales · Δ110d activos (de 120d cal.) · 109,09/día · -20d a fecha objetivo · "
        "Llegada 9818 · receso −20d · ⚠ lectura posterior a la fecha objetivo — "
        "interpolado hacia atrás"
    )


def test_par_entero_en_receso_usa_un_dia_minimo_sin_dividir_por_cero() -> None:
    entrada = make_input(
        real_anterior=lectura(0, date(2026, 3, 1)),
        ultimo_real=lectura(100, date(2026, 3, 20)),
        recesos=[receso(date(2026, 3, 1), date(2026, 3, 31))],
    )

    resultado = estimar(entrada)

    assert resultado.dias_par_pl == 1
    assert resultado.estim_propuesto == 3_100
    assert resultado.detalle_calculo == (
        "Entre dos reales · Δ1d activos (de 19d cal.) · 100/día · +30d a fecha objetivo · "
        "Llegada 3100 · receso −29d"
    )


def test_receso_fuera_del_intervalo_relevante_no_afecta() -> None:
    entrada = make_input(
        fecha_objetivo=date(2026, 3, 31),
        real_anterior=lectura(0, date(2026, 3, 1)),
        ultimo_real=lectura(6_000, date(2026, 3, 31)),
        ultimo_contador_facturado=lectura(0, date(2026, 3, 31)),
        recesos=[receso(date(2026, 6, 1), date(2026, 6, 30))],
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 6_000
    assert resultado.requiere_confirmacion is False


def test_receso_de_otro_anexo_no_aplica() -> None:
    entrada = make_input(
        **_PAR_CON_FEBRERO, recesos=[receso(date(2026, 2, 1), date(2026, 2, 28), id_anexo=99)]
    )

    assert estimar(entrada).estim_propuesto != 9_100


def test_receso_del_anexo_del_proceso_aplica_sin_mirar_el_grupo() -> None:
    entrada = make_input(
        **_PAR_CON_FEBRERO,
        recesos=[receso(date(2026, 2, 1), date(2026, 2, 28), id_grupo_economico=99, id_anexo=1)],
    )

    assert estimar(entrada).estim_propuesto == 9_100


def test_receso_por_grupo_economico_aplica_a_cualquier_anexo() -> None:
    entrada = make_input(
        **_PAR_CON_FEBRERO,
        id_anexo=2,
        recesos=[receso(date(2026, 2, 1), date(2026, 2, 28), id_grupo_economico=1, id_anexo=None)],
    )

    assert estimar(entrada).estim_propuesto == 9_100


def test_receso_de_otro_grupo_economico_no_aplica() -> None:
    entrada = make_input(
        **_PAR_CON_FEBRERO,
        id_anexo=2,
        recesos=[receso(date(2026, 2, 1), date(2026, 2, 28), id_grupo_economico=99, id_anexo=None)],
    )

    assert estimar(entrada).estim_propuesto != 9_100


def test_rama_de_parque_se_escala_por_dias_activos_del_periodo() -> None:
    entrada = make_input(
        periodo_desde=date(2026, 7, 1),
        periodo_hasta=date(2026, 7, 31),
        parque_cliente_modelo=parque(10_000),
        recesos=[receso(date(2026, 7, 2), date(2026, 7, 16))],
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 5_000
    assert resultado.ajustado_por_receso is True
    assert resultado.marcas == {"AjustadoPorReceso"}
    assert resultado.detalle_calculo == (
        "Sin historia propia · Parque del cliente · mismo modelo · Mediana truncada P80 · "
        "8 equipos (0 descartados) · +5000 imp · receso ×0,50 (de 10000 imp)"
    )
    assert resultado.etiqueta_nivel == "Parque del cliente · mismo modelo · ajustado por receso"


def test_parque_escalado_redondea_al_par() -> None:
    """Round(Round(10001) × 0,5) = Round(5000,5) = 5000 (bancario)."""
    entrada = make_input(
        periodo_desde=date(2026, 7, 1),
        periodo_hasta=date(2026, 7, 31),
        parque_cliente_modelo=parque(10_001),
        recesos=[receso(date(2026, 7, 2), date(2026, 7, 16))],
    )

    assert estimar(entrada).impresiones == 5_000


def test_parque_escalado_usa_la_aritmetica_de_system_decimal() -> None:
    """Factor 2/24 en `System.Decimal` es 0,0833…333 con 27 dígitos: 29634 ×
    factor = 2469,4999… → 2469 (con la precisión de Python daría 2469,5 → 2470).
    Caso hallado en el diferencial contra el motor v1.7 compilado."""
    entrada = make_input(
        periodo_desde=date(2026, 4, 8),
        periodo_hasta=date(2026, 5, 2),
        parque_cliente_modelo=parque(29_634, n_equipos=11, n_descartados=3),
        recesos=[receso(date(2026, 4, 11), date(2026, 5, 16))],
    )

    resultado = estimar(entrada)

    assert resultado.impresiones == 2_469
    assert "+2469 imp · receso ×0,08 (de 29634 imp)" in resultado.detalle_calculo


def test_receso_fuera_del_periodo_del_proceso_no_escala_el_parque() -> None:
    entrada = make_input(
        periodo_desde=date(2026, 7, 1),
        periodo_hasta=date(2026, 7, 31),
        parque_cliente_modelo=parque(10_000),
        recesos=[receso(date(2026, 12, 1), date(2026, 12, 15))],
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 10_000
    assert resultado.ajustado_por_receso is False
