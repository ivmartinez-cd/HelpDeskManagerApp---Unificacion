"""CASOS_DE_PRUEBA.md §6 — T4 (Servicio Técnico) como Llegada
(REGLAS_DE_NEGOCIO §5.3)."""

from datetime import date

import pytest

from src.modules.contadores.domain.services.estimacion.motor import estimar
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque


def test_t4_revisado_se_proyecta() -> None:
    entrada = make_input(
        ultimo_contador_facturado=lectura(95_000, date(2026, 3, 31)),
        t4_mas_reciente=lectura(105_000, date(2026, 4, 25), tipo_toma=4),
        t4_revisado=True,
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == pytest.approx(107_000)
    assert resultado.impresiones == pytest.approx(12_000)
    assert resultado.tipo_toma == 14
    assert resultado.fuente == "T4_ST"
    assert resultado.borde_salto_imposible is False
    assert resultado.requiere_confirmacion is False
    assert resultado.semaforo == "VERDE"


def test_t4_sin_revisar_mismo_calculo_con_aviso() -> None:
    entrada = make_input(
        ultimo_contador_facturado=lectura(95_000, date(2026, 3, 31)),
        t4_mas_reciente=lectura(105_000, date(2026, 4, 25), tipo_toma=4),
        t4_revisado=False,
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == pytest.approx(107_000)
    assert resultado.requiere_confirmacion is True
    assert resultado.semaforo == "AMARILLO"


def test_t4_le_gana_al_parque_sin_par_de_reales_propio() -> None:
    entrada = make_input(
        ultimo_contador_facturado=lectura(95_000, date(2026, 3, 31)),
        t4_mas_reciente=lectura(105_000, date(2026, 4, 25), tipo_toma=4),
        t4_revisado=False,
        parque_cliente_modelo=parque(20_000),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "T4_ST"


def test_con_ultimo_real_se_prefiere_como_partida_sobre_facturado() -> None:
    entrada = make_input(
        ultimo_contador_facturado=lectura(95_000, date(2026, 2, 28)),
        ultimo_real=lectura(100_000, date(2026, 3, 26)),
        t4_mas_reciente=lectura(105_000, date(2026, 4, 25), tipo_toma=4),
        t4_revisado=True,
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == pytest.approx(105_833.33, abs=0.5)
    assert resultado.dias_par_pl == 30


def test_sin_partida_valida_usa_el_valor_tal_cual_con_nota() -> None:
    entrada = make_input(
        ultimo_contador_facturado=lectura(90_000, date(2026, 4, 20)),
        t4_mas_reciente=lectura(105_000, date(2026, 4, 25), tipo_toma=4),
        t4_revisado=True,
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 105_000
    assert resultado.metodo_detalle == "T4ST valor"
    assert resultado.requiere_confirmacion is True
    assert resultado.nota_operador is not None


def test_backup_nunca_se_proyecta() -> None:
    entrada = make_input(
        estado_maquina="BACKUP",
        ultimo_contador_facturado=lectura(95_000, date(2026, 3, 31)),
        t4_mas_reciente=lectura(105_000, date(2026, 4, 25), tipo_toma=4),
        t4_revisado=True,
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 105_000
    assert resultado.nota_operador is None


def test_t4_viejo_sin_real_previo_cae_al_parque() -> None:
    entrada = make_input(
        ultimo_contador_facturado=lectura(50_000, date(2025, 8, 1)),
        t4_mas_reciente=lectura(60_000, date(2025, 8, 25), tipo_toma=4),
        t4_revisado=False,
        parque_cliente_modelo=parque(20_000),
    )

    resultado = estimar(entrada)

    assert resultado.fuente != "T4_ST"


def test_t4_en_el_par_entre_reales_dispara_amarillo() -> None:
    entrada = make_input(
        real_anterior=lectura(50_000, date(2025, 9, 12), tipo_toma=1),
        ultimo_real=lectura(60_000, date(2026, 4, 27), tipo_toma=4),
        ultimo_contador_facturado=lectura(50_000, date(2025, 9, 12)),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Historia_Propia"
    assert resultado.requiere_confirmacion is True
    assert resultado.semaforo == "AMARILLO"


def test_backup_con_t4_anterior_al_ultimo_real_no_se_usa() -> None:
    entrada = make_input(
        estado_maquina="BACKUP",
        fecha_ultimo_real_no_t4=date(2026, 3, 15),
        t4_mas_reciente=lectura(277_160, date(2026, 2, 10), tipo_toma=4),
        t4_revisado=False,
        ultimo_contador_facturado=lectura(277_160, date(2026, 3, 15)),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Backup_SinST"
    assert resultado.impresiones == 0


def test_t4_corrector_posterior_al_real_se_usa_aunque_de_negativo() -> None:
    entrada = make_input(
        fecha_ultimo_real_no_t4=date(2026, 2, 1),
        t4_mas_reciente=lectura(1_260, date(2026, 4, 10), tipo_toma=4),
        t4_revisado=False,
        ultimo_contador_facturado=lectura(1_300, date(2026, 4, 1)),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "T4_ST"
    assert resultado.impresiones is not None and resultado.impresiones < 0
