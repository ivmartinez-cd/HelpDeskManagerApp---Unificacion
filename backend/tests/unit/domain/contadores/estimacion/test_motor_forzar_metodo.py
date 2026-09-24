"""`ForzarEntreReales` / `ForzarCascada` del legacy."""

from datetime import date

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


def test_forzar_entre_reales_da_lo_mismo_que_el_automatico_con_prefijo() -> None:
    entrada = make_input(
        real_anterior=lectura(0, date(2026, 1, 1)),
        ultimo_real=lectura(6_200, date(2026, 4, 1)),
        ultimo_contador_facturado=lectura(0, date(2026, 4, 1)),
        recesos=[receso(date(2026, 2, 1), date(2026, 2, 28))],
    )

    resultado = forzar_entre_reales(make_ctx(entrada))

    assert resultado is not None
    assert resultado.estim_propuesto == 9_100
    assert resultado.semaforo == "AMARILLO"
    assert resultado.marcas == {"AjustadoPorReceso", "ForzadoPorOperador"}
    assert resultado.detalle_calculo == (
        "Forzado a entre reales por operador · Entre dos reales · Δ62d activos (de 90d cal.) · "
        "100/día · +29d a fecha objetivo · Llegada 9100 · receso −28d"
    )


def test_forzar_entre_reales_ignora_historia_en_alerta() -> None:
    entrada = make_input(
        real_anterior=lectura(100_000, date(2024, 1, 1)),
        ultimo_real=lectura(130_000, date(2024, 3, 1)),
        ultimo_contador_facturado=lectura(120_000, date(2024, 3, 1)),
        parque_cliente_tecnologia=parque(10_000),
    )

    resultado = forzar_entre_reales(make_ctx(entrada))

    assert resultado is not None
    assert resultado.fuente == "Historia_Propia"
    assert resultado.meses_sin_real_en_alerta is True


def test_forzar_entre_reales_conserva_un_negativo() -> None:
    entrada = make_input(
        real_anterior=lectura(1_000, date(2026, 1, 1)),
        ultimo_real=lectura(1_100, date(2026, 3, 1)),
        ultimo_contador_facturado=lectura(5_000, date(2026, 3, 31)),
    )

    resultado = forzar_entre_reales(make_ctx(entrada))

    assert resultado is not None
    assert resultado.estim_propuesto == 1_202
    assert resultado.impresiones == -3_798


def test_forzar_entre_reales_sin_par_da_none() -> None:
    assert forzar_entre_reales(make_ctx(make_input())) is None


def test_forzar_entre_reales_separacion_menor_a_15_dias_da_none() -> None:
    entrada = make_input(
        real_anterior=lectura(125_000, date(2026, 3, 21)),
        ultimo_real=lectura(130_000, date(2026, 3, 31)),
    )

    assert forzar_entre_reales(make_ctx(entrada)) is None


def test_forzar_entre_reales_con_contador_quieto_da_none() -> None:
    entrada = make_input(
        real_anterior=lectura(50_000, date(2026, 2, 1)),
        ultimo_real=lectura(50_000, date(2026, 3, 31)),
    )

    assert forzar_entre_reales(make_ctx(entrada)) is None


def test_forzar_cascada_ignora_que_habia_un_par_de_reales_mejor() -> None:
    entrada = make_input(
        real_anterior=lectura(100_000, date(2026, 2, 1)),
        ultimo_real=lectura(130_000, date(2026, 3, 31)),
        ultimo_contador_facturado=lectura(120_000, date(2026, 3, 31)),
        parque_cliente_modelo=parque(11_000),
    )

    resultado = forzar_cascada_parque(make_ctx(entrada))

    assert resultado.fuente == "Parque_Cliente_Modelo"
    assert resultado.estim_propuesto == 131_000
    assert resultado.tipo_toma == 19
    assert resultado.semaforo == "ROJO"
    assert resultado.marcas == {"ForzadoPorOperador"}
    assert resultado.detalle_calculo == (
        "Forzado a T19 (cascada) por operador · Historia propia vieja (0m sin real) · "
        "Parque del cliente · mismo modelo · Mediana truncada P80 · 8 equipos (0 descartados) · "
        "+11000 imp"
    )


def test_forzar_cascada_sin_ningun_nivel_deja_la_fila_pendiente() -> None:
    resultado = forzar_cascada_parque(make_ctx(make_input()))

    assert resultado.fuente == "Pendiente"
    assert resultado.marcas == frozenset()  # sin decisión en el legacy: no hay dónde marcar
    assert resultado.estim_propuesto is None
    assert resultado.semaforo == "ROJO"
    assert resultado.detalle_calculo == (
        "Forzado a T19 (cascada) por operador · "
        "Sin datos suficientes para estimar — marcar pendiente."
    )


def test_forzar_cascada_sobre_una_fila_ya_real_queda_verde() -> None:
    entrada = make_input(
        pendiente_estimar=False,
        ultimo_contador_facturado=lectura(1_000, date(2026, 3, 31)),
        parque_cliente_modelo=parque(11_000),
    )

    resultado = forzar_cascada_parque(make_ctx(entrada))

    assert resultado.fuente == "Parque_Cliente_Modelo"
    assert resultado.semaforo == "VERDE"
