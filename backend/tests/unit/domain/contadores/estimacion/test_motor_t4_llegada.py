"""T4 (Servicio Técnico) como Llegada y equipos sin movimiento
(`EstimarConT4ST` / `CrearSinMovimiento` del legacy v1.7): el T4 se proyecta
a la fecha objetivo con regla de tres cuando hay Partida válida; sin ella (o
en un Backup) se toma tal cual. El tipo de toma sugerido es SIEMPRE 14.
Casos portados de `CalculadorContadoresTests.cs` (sección 5)."""

from datetime import date

from src.modules.contadores.domain.services.estimacion.motor import estimar
from src.modules.contadores.domain.services.estimacion.t4_como_llegada import NOTA_SIN_PAR
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque, receso

_T4 = lectura(105_000, date(2026, 4, 25), tipo_toma=4)
_FACTURADO = lectura(95_000, date(2026, 3, 31))


def test_t4_revisado_se_proyecta_a_fecha_objetivo_con_tipo_14() -> None:
    # P = últ. facturado 95.000 (31/03), L = T4 105.000 (25/04): 400/día, +5d.
    entrada = make_input(
        ultimo_contador_facturado=_FACTURADO, t4_mas_reciente=_T4, t4_revisado=True
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 107_000
    assert resultado.impresiones == 12_000
    assert resultado.tipo_toma == 14
    assert resultado.fuente == "T4_ST"
    assert resultado.metodo == "T4ST_Proyectado"
    assert resultado.marcas == frozenset()
    assert resultado.requiere_confirmacion is False
    assert resultado.t4_sin_revisar is False
    assert resultado.semaforo == "VERDE"
    assert resultado.dias_par_pl == 25
    assert resultado.tasa_diaria == 400
    assert resultado.dias_proyectados == 5
    assert resultado.detalle_calculo == (
        "T4 ST proyectado · P:31/03/26=95000 (últ. facturado) · L(T4):25/04/26=105000 · "
        "Δ25d activos · 400/día · +5d a fecha objetivo · T4 revisado (Para_Facturar>0)"
    )
    assert resultado.etiqueta_nivel == (
        "T4 ST proyectado · Partida: últ. facturado · T4 revisado (Para_Facturar>0)"
    )


def test_t4_sin_revisar_se_proyecta_igual_pero_a_confirmar() -> None:
    entrada = make_input(
        ultimo_contador_facturado=_FACTURADO, t4_mas_reciente=_T4, t4_revisado=False
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 107_000
    assert resultado.tipo_toma == 14
    assert resultado.requiere_confirmacion is True
    assert resultado.t4_sin_revisar is True
    assert resultado.marcas == {"T4SinRevisar"}
    assert resultado.semaforo == "AMARILLO"
    assert resultado.detalle_calculo.endswith(" · ⚠ T4 SIN revisar (Para_Facturar=0) — confirmar")


def test_t4_le_gana_al_parque_sin_par_de_reales_propio() -> None:
    entrada = make_input(
        ultimo_contador_facturado=_FACTURADO,
        t4_mas_reciente=_T4,
        parque_cliente_modelo=parque(20_000),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "T4_ST"
    assert resultado.estim_propuesto == 107_000


def test_con_ultimo_real_lo_usa_como_partida_en_vez_del_facturado() -> None:
    # 5.000 en 30d = 166,67/día → 105.000 + 5 × 166,67 ≈ 105.833.
    entrada = make_input(
        ultimo_contador_facturado=lectura(95_000, date(2026, 2, 28)),
        ultimo_real=lectura(100_000, date(2026, 3, 26)),
        t4_mas_reciente=_T4,
        t4_revisado=True,
    )

    resultado = estimar(entrada)

    assert resultado.tipo_toma == 14
    assert resultado.estim_propuesto == 105_833
    assert resultado.dias_par_pl == 30
    assert "(últ. real)" in resultado.detalle_calculo
    assert "166,67/día" in resultado.detalle_calculo


def test_ultimo_real_mayor_al_t4_no_sirve_de_partida_y_usa_el_facturado() -> None:
    entrada = make_input(
        ultimo_contador_facturado=_FACTURADO,
        ultimo_real=lectura(106_000, date(2026, 3, 1)),
        t4_mas_reciente=_T4,
        t4_revisado=True,
    )

    assert "(últ. facturado)" in estimar(entrada).detalle_calculo


def test_sin_partida_valida_propone_el_t4_tal_cual_con_nota_para_el_operador() -> None:
    # El últ. facturado está a 5 días del T4 (< 15d): no hay par para proyectar.
    entrada = make_input(
        ultimo_contador_facturado=lectura(95_000, date(2026, 4, 20)),
        t4_mas_reciente=_T4,
        t4_revisado=True,
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 105_000
    assert resultado.impresiones == 10_000
    assert resultado.tipo_toma == 14
    assert resultado.metodo == "T4ST_Valor"
    assert resultado.marcas == {"SinParValido"}
    assert resultado.requiere_confirmacion is True
    assert resultado.semaforo == "AMARILLO"
    assert resultado.nota_operador == NOTA_SIN_PAR
    assert resultado.detalle_calculo == (
        "T4 ST tal cual como Llegada — sin par válido para proyectar (P/L < 15d o P > L) · "
        "T4 revisado (Para_Facturar>0)"
    )
    assert resultado.etiqueta_nivel == resultado.detalle_calculo


def test_t4_proyectado_con_receso_pide_confirmacion() -> None:
    entrada = make_input(
        ultimo_contador_facturado=lectura(0, date(2026, 1, 1)),
        t4_mas_reciente=lectura(6_200, date(2026, 4, 1), tipo_toma=4),
        t4_revisado=True,
        recesos=[receso(date(2026, 2, 1), date(2026, 2, 28))],
    )

    resultado = estimar(entrada)

    assert resultado.estim_propuesto == 9_100
    assert resultado.requiere_confirmacion is True
    assert resultado.marcas == {"AjustadoPorReceso"}
    assert resultado.semaforo == "AMARILLO"
    # El detalle del T4 no lleva la nota "receso −Nd" ni los días calendario.
    assert resultado.detalle_calculo == (
        "T4 ST proyectado · P:01/01/26=0 (últ. facturado) · L(T4):01/04/26=6200 · "
        "Δ62d activos · 100/día · +29d a fecha objetivo · T4 revisado (Para_Facturar>0)"
    )


def test_t4_viejo_sin_real_previo_cae_al_parque() -> None:
    entrada = make_input(
        ultimo_contador_facturado=lectura(379, date(2025, 8, 31)),
        t4_mas_reciente=lectura(198, date(2025, 9, 4), tipo_toma=4),
        parque_cliente_modelo=parque(120),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Parque_Cliente_Modelo"
    assert resultado.impresiones is not None and resultado.impresiones >= 0


def test_t4_en_el_par_entre_reales_pide_confirmacion() -> None:
    entrada = make_input(
        real_anterior=lectura(50_000, date(2025, 9, 12)),
        ultimo_real=lectura(60_000, date(2026, 4, 27), tipo_toma=4),
        ultimo_contador_facturado=lectura(50_000, date(2025, 9, 12)),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Historia_Propia"
    assert resultado.estim_propuesto == 60_132
    assert resultado.par_incluye_t4 is True
    assert resultado.marcas == {"UsaT4EnPar"}
    assert resultado.semaforo == "AMARILLO"
    assert resultado.detalle_calculo.endswith(" · ⚠ usa T4 (Informe S. Técnico) — confirmar")


def test_t4_corrector_posterior_al_real_se_usa_aunque_de_negativo() -> None:
    # Facturado a 9 días del T4: sin Partida válida → tal cual, negativo.
    entrada = make_input(
        fecha_ultimo_real_no_t4=date(2026, 2, 1),
        t4_mas_reciente=lectura(1_260, date(2026, 4, 10), tipo_toma=4),
        ultimo_contador_facturado=lectura(1_300, date(2026, 4, 1)),
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "T4_ST"
    assert resultado.impresiones == -40
    assert resultado.marcas == {"T4SinRevisar", "SinParValido"}


def test_backup_con_t4_valido_no_proyecta_y_graba_t14() -> None:
    entrada = make_input(
        estado_maquina="BACKUP",
        ultimo_contador_facturado=_FACTURADO,
        t4_mas_reciente=_T4,
        t4_revisado=True,
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "T4_ST"
    assert resultado.tipo_toma == 14
    assert resultado.metodo == "T4ST_Valor"
    assert resultado.estim_propuesto == 105_000
    assert resultado.nota_operador is None
    assert resultado.requiere_confirmacion is False
    assert resultado.semaforo == "VERDE"
    assert resultado.detalle_calculo == (
        "T4 ST revisado (Para_Facturar>0) como Llegada — dato confiable."
    )


def test_backup_con_t4_sin_revisar_pide_confirmacion() -> None:
    entrada = make_input(
        estado_maquina="BACKUP",
        ultimo_contador_facturado=_FACTURADO,
        t4_mas_reciente=_T4,
        t4_revisado=False,
    )

    resultado = estimar(entrada)

    assert resultado.marcas == {"T4SinRevisar"}
    assert resultado.semaforo == "AMARILLO"
    assert resultado.detalle_calculo == (
        "T4 ST SIN revisar (Para_Facturar=0) como Llegada — confirmar antes de facturar."
    )


def test_backup_con_t4_anterior_al_ultimo_real_repite_el_contador() -> None:
    entrada = make_input(
        estado_maquina="BACKUP",
        fecha_ultimo_real_no_t4=date(2026, 3, 15),
        t4_mas_reciente=lectura(277_160, date(2026, 2, 10), tipo_toma=4),
        ultimo_contador_facturado=lectura(279_764, date(2026, 3, 31)),
        prom_6_facturados=1_000,
    )

    resultado = estimar(entrada)

    assert resultado.fuente == "Backup_SinST"
    assert resultado.metodo == "ContadorAnterior"
    assert resultado.estim_propuesto == 279_764
    assert resultado.impresiones == 0
    assert resultado.tipo_toma == 14
    assert resultado.requiere_confirmacion is True
    assert resultado.coloreo == "NORMAL"
    assert resultado.semaforo == "AMARILLO"
    assert resultado.detalle_calculo == (
        "Backup sin T4 ST — sin movimiento, se repite contador anterior."
    )


def test_en_transito_sin_contador_anterior_propone_vacio() -> None:
    entrada = make_input(estado_maquina="EN_TRANSITO", ultimo_contador_facturado=None)

    resultado = estimar(entrada)

    assert resultado.fuente == "EnTransito"
    assert resultado.estim_propuesto is None
    assert resultado.impresiones == 0
    assert resultado.tipo_toma == 14
    assert resultado.semaforo == "AMARILLO"
    assert resultado.detalle_calculo == (
        "En tránsito a taller — sin movimiento, se repite contador anterior."
    )
