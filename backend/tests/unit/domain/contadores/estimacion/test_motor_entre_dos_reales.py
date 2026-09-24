"""Fila ya real y "entre dos reales" (`Calcular` / `EstimarEntreReales` del
legacy). Valores esperados sacados del C# legacy: `Math.Round` bancario sobre
decimal y `DetalleCalculo` en es-AR."""

from datetime import date

from src.modules.contadores.domain.services.estimacion.motor import estimar
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque


def test_lectura_real_no_estima_y_devuelve_las_impresiones_reales() -> None:
    entrada = make_input(pendiente_estimar=False, impresiones_reales=4_321)

    resultado = estimar(entrada)

    assert resultado.estim_propuesto is None
    assert resultado.impresiones == 4_321
    assert resultado.tipo_toma is None
    assert resultado.semaforo == "VERDE"
    assert resultado.fuente == "Sin_Estimar"
    assert resultado.metodo == "NoAplica"
    assert resultado.detalle_calculo == "Lectura real registrada para el período."


def test_entre_dos_reales_redondea_a_entero_y_arma_el_detalle() -> None:
    entrada = make_input(
        real_anterior=lectura(100_000, date(2026, 2, 1)),
        ultimo_real=lectura(130_000, date(2026, 3, 31)),
        ultimo_contador_facturado=lectura(120_000, date(2026, 3, 31)),
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 145_517
    assert resultado.impresiones == 25_517
    assert resultado.tipo_toma == 14
    assert resultado.fuente == "Historia_Propia"
    assert resultado.requiere_confirmacion is False
    assert resultado.semaforo == "VERDE"
    assert resultado.tasa_diaria == 517.24
    assert resultado.metodo == "EntreReales"
    assert resultado.marcas == frozenset()
    assert resultado.detalle_calculo == (
        "Entre dos reales · Δ58d activos · 517,24/día · +30d a fecha objetivo · "
        "Llegada 145517"
    )
    assert resultado.etiqueta_nivel == "Entre dos lecturas reales del propio equipo"


def test_redondeo_bancario_en_el_valor_y_lejos_del_cero_en_el_texto() -> None:
    """Llegada proyectada 102,5: `Math.Round` da 102 (al par) pero el texto
    `{x:0}` de .NET redondea el medio para arriba y muestra 103."""
    entrada = make_input(
        fecha_objetivo=date(2026, 4, 11),
        real_anterior=lectura(0, date(2026, 3, 1)),
        ultimo_real=lectura(100, date(2026, 4, 10)),
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 102
    assert resultado.impresiones == 102
    assert resultado.detalle_calculo == (
        "Entre dos reales · Δ40d activos · 2,5/día · +1d a fecha objetivo · Llegada 103"
    )


def test_sin_contador_anterior_las_impresiones_son_todo_el_estimado() -> None:
    entrada = make_input(
        real_anterior=lectura(100_000, date(2026, 2, 1)),
        ultimo_real=lectura(130_000, date(2026, 3, 31)),
        ultimo_contador_facturado=None,
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 145_517
    assert resultado.impresiones == 145_517


def test_interpolacion_hacia_atras_solo_avisa_y_el_valor_sale() -> None:
    entrada = make_input(
        fecha_objetivo=date(2026, 5, 31),
        real_anterior=lectura(26_579, date(2026, 3, 17)),
        ultimo_real=lectura(43_226, date(2026, 6, 16)),
        ultimo_contador_facturado=lectura(30_884, date(2026, 5, 1)),
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 40_299
    assert resultado.impresiones == 9_415
    assert resultado.dias_proyectados == -16
    assert resultado.marcas == {"InterpoladoAtras"}
    assert resultado.requiere_confirmacion is False
    assert resultado.semaforo == "VERDE"
    assert resultado.detalle_calculo == (
        "Entre dos reales · Δ91d activos · 182,93/día · -16d a fecha objetivo · "
        "Llegada 40299 · ⚠ lectura posterior a la fecha objetivo — interpolado hacia atrás"
    )


def test_separacion_menor_a_15_dias_descarta_el_par() -> None:
    entrada = make_input(
        real_anterior=lectura(125_000, date(2026, 3, 21)),
        ultimo_real=lectura(130_000, date(2026, 3, 31)),
        parque_cliente_tecnologia=parque(10_000, n_equipos=8),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Cliente_Tec"
    assert resultado.tipo_toma == 19


def test_contador_sin_movimiento_entre_reales_no_sirve_de_par() -> None:
    """`PuedeCalcularEntreReales` exige último real ESTRICTAMENTE mayor: con
    el contador quieto no estima +0, cae a la cascada."""
    entrada = make_input(
        real_anterior=lectura(50_000, date(2026, 2, 1)),
        ultimo_real=lectura(50_000, date(2026, 3, 31)),
        ultimo_contador_facturado=lectura(50_000, date(2026, 3, 31)),
        parque_cliente_tecnologia=parque(10_000, n_equipos=8),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Cliente_Tec"
    assert resultado.estim_propuesto == 60_000


def test_negativo_entre_reales_se_descarta_y_cae_a_la_cascada() -> None:
    entrada = make_input(
        real_anterior=lectura(1_000, date(2026, 1, 1)),
        ultimo_real=lectura(1_100, date(2026, 3, 1)),
        ultimo_contador_facturado=lectura(5_000, date(2026, 3, 31)),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Pendiente"
    assert resultado.estim_propuesto is None


def test_negativo_se_conserva_si_el_ultimo_real_es_un_t4_valido() -> None:
    entrada = make_input(
        real_anterior=lectura(1_000, date(2026, 1, 1)),
        ultimo_real=lectura(1_100, date(2026, 3, 1), tipo_toma=4),
        fecha_ultimo_real_no_t4=date(2026, 1, 1),
        ultimo_contador_facturado=lectura(5_000, date(2026, 3, 31)),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Historia_Propia"
    assert resultado.estim_propuesto == 1_202
    assert resultado.impresiones == -3_798
    assert resultado.requiere_confirmacion is True
    assert resultado.semaforo == "AMARILLO"
    assert resultado.detalle_calculo == (
        "Entre dos reales · Δ59d activos · 1,69/día · +60d a fecha objetivo · "
        "Llegada 1202 · ⚠ usa T4 (Informe S. Técnico) — confirmar"
    )
    assert resultado.etiqueta_nivel == (
        "Entre dos lecturas reales del propio equipo (incluye un T4)"
    )
