"""CASOS_DE_PRUEBA.md §5 — ajuste por recesos del cliente (REGLAS_DE_NEGOCIO §6)."""

from datetime import date

import pytest

from src.modules.contadores.domain.services.estimacion.motor import estimar
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque, receso


def test_receso_entre_los_reales_no_diluye_la_tasa() -> None:
    entrada = make_input(
        real_anterior=lectura(0, date(2026, 1, 1)),
        ultimo_real=lectura(6_200, date(2026, 4, 1)),
        ultimo_contador_facturado=lectura(0, date(2026, 4, 1)),
        recesos=[receso(date(2026, 2, 1), date(2026, 2, 28))],
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == pytest.approx(9_100)
    assert resultado.requiere_confirmacion is True


def test_receso_en_ventana_de_proyeccion_no_factura_el_receso() -> None:
    entrada = make_input(
        fecha_objetivo=date(2026, 1, 31),
        real_anterior=lectura(0, date(2025, 11, 1)),
        ultimo_real=lectura(6_000, date(2025, 12, 1)),
        ultimo_contador_facturado=lectura(0, date(2025, 12, 1)),
        recesos=[receso(date(2025, 12, 15), date(2026, 1, 15))],
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == pytest.approx(11_800)


def test_receso_fuera_del_intervalo_relevante_no_afecta() -> None:
    entrada = make_input(
        fecha_objetivo=date(2026, 3, 31),
        real_anterior=lectura(0, date(2026, 3, 1)),
        ultimo_real=lectura(6_000, date(2026, 3, 31)),
        ultimo_contador_facturado=lectura(0, date(2026, 3, 31)),
        recesos=[receso(date(2026, 6, 1), date(2026, 6, 30))],
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == pytest.approx(6_000)
    assert resultado.requiere_confirmacion is False


def test_receso_de_otro_anexo_no_aplica() -> None:
    entrada = make_input(
        real_anterior=lectura(0, date(2026, 1, 1)),
        ultimo_real=lectura(6_200, date(2026, 4, 1)),
        ultimo_contador_facturado=lectura(0, date(2026, 4, 1)),
        recesos=[receso(date(2026, 2, 1), date(2026, 2, 28), id_anexo=99)],
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto != pytest.approx(9_100)


def test_receso_por_grupo_economico_aplica_a_cualquier_anexo() -> None:
    entrada = make_input(
        id_anexo=2,
        real_anterior=lectura(0, date(2026, 1, 1)),
        ultimo_real=lectura(6_200, date(2026, 4, 1)),
        ultimo_contador_facturado=lectura(0, date(2026, 4, 1)),
        recesos=[receso(date(2026, 2, 1), date(2026, 2, 28), id_grupo_economico=1, id_anexo=None)],
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == pytest.approx(9_100)


def test_receso_de_otro_grupo_economico_no_aplica() -> None:
    entrada = make_input(
        id_anexo=2,
        real_anterior=lectura(0, date(2026, 1, 1)),
        ultimo_real=lectura(6_200, date(2026, 4, 1)),
        ultimo_contador_facturado=lectura(0, date(2026, 4, 1)),
        recesos=[receso(date(2026, 2, 1), date(2026, 2, 28), id_grupo_economico=99, id_anexo=None)],
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto != pytest.approx(9_100)


def test_rama_de_parque_se_escala_por_dias_activos_del_periodo() -> None:
    entrada = make_input(
        periodo_desde=date(2026, 7, 1),
        periodo_hasta=date(2026, 7, 31),
        ultimo_contador_facturado=lectura(0, date(2026, 6, 30)),
        parque_cliente_modelo=parque(10_000),
        recesos=[receso(date(2026, 7, 2), date(2026, 7, 16))],
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == pytest.approx(5_000)


def test_receso_fuera_del_periodo_del_proceso_no_escala_el_parque() -> None:
    entrada = make_input(
        periodo_desde=date(2026, 7, 1),
        periodo_hasta=date(2026, 7, 31),
        ultimo_contador_facturado=lectura(0, date(2026, 6, 30)),
        parque_cliente_modelo=parque(10_000),
        recesos=[receso(date(2026, 12, 1), date(2026, 12, 15))],
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == pytest.approx(10_000)
