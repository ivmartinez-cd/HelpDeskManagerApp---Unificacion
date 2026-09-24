"""Restauración de la decisión del operador sobre una fila, como el legacy
(`GrillaEstimacion.RestaurarOverridesAsync` / `ReconstruirOverrideAsync`):
el método se vuelve a correr con los datos del día, no se congela un valor."""

from dataclasses import replace
from datetime import UTC, date, datetime

from src.modules.contadores.application.dtos.decision_operador_dto import (
    DecisionOperadorDto,
    LecturaElegidaDto,
)
from src.modules.contadores.application.use_cases._resolver_resultado_final import (
    contador_anterior_de,
    decision_no_descartada,
    decisiones_no_descartadas,
    resolver_resultado_final,
    resultado_pendiente_por_operador,
)
from src.modules.contadores.domain.services.estimacion.motor import estimar
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque

# Entre dos reales: 90 días, +9.000 → 100/día, +29 días hasta la fecha objetivo.
_ENTRE_REALES = make_input(
    real_anterior=lectura(10_000, date(2026, 1, 1)),
    ultimo_real=lectura(19_000, date(2026, 4, 1)),
    ultimo_contador_facturado=lectura(19_000, date(2026, 4, 1)),
    parque_cliente_tecnologia=parque(3_000),
)
_SIN_PAR = make_input(
    ultimo_contador_facturado=lectura(50_000, date(2026, 3, 31)),
    parque_cliente_tecnologia=parque(3_000),
)
_REAL = make_input(
    pendiente_estimar=False,
    ultimo_contador_facturado=lectura(118_500, date(2026, 3, 31)),
    impresiones_reales=3_800,
)


def _pl(partida: LecturaElegidaDto, llegada: LecturaElegidaDto) -> DecisionOperadorDto:
    return DecisionOperadorDto("PL_Manual", partida=partida, llegada=llegada)


def test_sin_decision_sale_el_automatico() -> None:
    resuelta = resolver_resultado_final(_ENTRE_REALES, None)

    assert resuelta.resultado == estimar(_ENTRE_REALES)
    assert resuelta.estado_decision == "ninguna"


def test_aceptar_sugerencia_no_se_restaura_ni_se_cuenta() -> None:
    decision = DecisionOperadorDto("AceptarSugerencia")

    resuelta = resolver_resultado_final(_ENTRE_REALES, decision)

    assert resuelta.resultado == estimar(_ENTRE_REALES)
    assert resuelta.estado_decision == "ninguna"


def test_fila_ya_real_descarta_la_decision_y_muestra_la_real() -> None:
    resuelta = resolver_resultado_final(_REAL, DecisionOperadorDto("MarcarPendiente"))

    assert resuelta.estado_decision == "descartada"
    assert resuelta.resultado.estim_propuesto is None
    assert resuelta.resultado.impresiones == 3_800
    assert resuelta.resultado.semaforo == "VERDE"


def test_fila_ya_real_con_aceptar_sugerencia_no_cuenta_como_descartada() -> None:
    resuelta = resolver_resultado_final(_REAL, DecisionOperadorDto("AceptarSugerencia"))

    assert resuelta.estado_decision == "ninguna"


def test_marcar_pendiente_deja_la_fila_en_blanco_como_construir_pendiente() -> None:
    resuelta = resolver_resultado_final(_ENTRE_REALES, DecisionOperadorDto("MarcarPendiente"))

    r = resuelta.resultado
    assert resuelta.estado_decision == "restaurada"
    assert (r.estim_propuesto, r.impresiones, r.tipo_toma) == (None, None, None)
    assert r.fuente == "Pendiente"
    assert r.semaforo == "ROJO"
    assert r.requiere_confirmacion is False
    assert r.borde_salto_imposible is False
    assert r.coloreo == "NORMAL"
    assert r.detalle_calculo == "Marcado pendiente por operador."


def test_marcar_pendiente_borra_la_guia_para_el_operador_y_conserva_el_resto() -> None:
    """`ConstruirPendiente`: `NotaOperador = null`; `Decision` (método,
    composición) y "meses sin real" quedan como estaban."""
    base = replace(estimar(_ENTRE_REALES), nota_operador="Elegí P/L a mano", dias_par_pl=90)

    r = resultado_pendiente_por_operador(base)

    assert r.nota_operador is None
    assert (r.dias_par_pl, r.metodo) == (90, base.metodo)
    assert r.meses_sin_real_en_alerta == base.meses_sin_real_en_alerta


def test_contador_anterior_para_auditar_es_cero_sin_contador_facturado() -> None:
    """`ContadorAnterior_Valor ?? 0m` de `EscribirAudit`."""
    assert contador_anterior_de(_ENTRE_REALES) == 19_000
    assert contador_anterior_de(replace(_SIN_PAR, ultimo_contador_facturado=None)) == 0


def test_forzar_cascada_se_recalcula_con_los_datos_del_dia() -> None:
    decision = DecisionOperadorDto("ForzarCascada")

    antes = resolver_resultado_final(_ENTRE_REALES, decision)
    otro_parque = replace(_ENTRE_REALES, parque_cliente_tecnologia=parque(4_000))
    despues = resolver_resultado_final(otro_parque, decision)

    assert antes.estado_decision == "restaurada"
    assert antes.resultado.tipo_toma == 19
    assert antes.resultado.detalle_calculo.startswith("Forzado a T19 (cascada) por operador · ")
    assert antes.resultado.estim_propuesto == 22_000
    assert despues.resultado.estim_propuesto == 23_000


def test_forzar_entre_reales_sin_par_valido_se_descarta() -> None:
    resuelta = resolver_resultado_final(_SIN_PAR, DecisionOperadorDto("ForzarEntreReales"))

    assert resuelta.estado_decision == "descartada"
    assert resuelta.resultado == estimar(_SIN_PAR)


def test_forzar_entre_reales_con_par_se_restaura() -> None:
    resuelta = resolver_resultado_final(_ENTRE_REALES, DecisionOperadorDto("ForzarEntreReales"))

    assert resuelta.estado_decision == "restaurada"
    assert resuelta.resultado.detalle_calculo.startswith("Forzado a entre reales por operador · ")


def test_pl_manual_se_recalcula_con_la_pareja_guardada() -> None:
    decision = _pl(
        LecturaElegidaDto(date(2026, 1, 31), 40_000, 1, id_contador=11),
        LecturaElegidaDto(date(2026, 3, 2), 43_000, 1, id_contador=12),
    )

    resuelta = resolver_resultado_final(_SIN_PAR, decision)

    r = resuelta.resultado
    assert resuelta.estado_decision == "restaurada"
    assert r.fuente == "Historia_Propia"
    assert r.tipo_toma == 14
    # 3.000 en 30 días → 100/día; Llegada + 59 días hasta el 30/04.
    assert r.estim_propuesto == 48_900
    assert r.detalle_calculo.startswith("P/L manual · P:31/01/26=40000 · L:02/03/26=43000")


def test_pl_manual_con_llegada_t4_sugiere_t14_nunca_t4() -> None:
    """v1.7 (`RecalcularConPL`, fix 02/07/26): el estimador graba SIEMPRE
    T14; la fuente T4_ST y el borde amarillo quedan por trazabilidad."""
    decision = _pl(
        LecturaElegidaDto(date(2026, 1, 31), 40_000, 1),
        LecturaElegidaDto(date(2026, 3, 2), 43_000, 4, para_facturar=False),
    )

    r = resolver_resultado_final(_SIN_PAR, decision).resultado

    assert (r.tipo_toma, r.fuente, r.t4_sin_revisar) == (14, "T4_ST", True)


def test_pl_manual_invalida_se_descarta() -> None:
    """Menos de 15 días entre Partida y Llegada: `RecalcularConPL` devuelve
    la fila sin cambios y la restauración la descarta."""
    decision = _pl(
        LecturaElegidaDto(date(2026, 3, 1), 40_000, 1),
        LecturaElegidaDto(date(2026, 3, 10), 43_000, 1),
    )

    resuelta = resolver_resultado_final(_SIN_PAR, decision)

    assert resuelta.estado_decision == "descartada"
    assert resuelta.resultado == estimar(_SIN_PAR)


def test_pl_manual_con_una_lectura_que_ya_no_esta_se_descarta() -> None:
    decision = DecisionOperadorDto(
        "PL_Manual", llegada=LecturaElegidaDto(date(2026, 3, 2), 43_000, 1, id_contador=12)
    )

    assert resolver_resultado_final(_SIN_PAR, decision).estado_decision == "descartada"


def test_descartar_hasta_deja_afuera_solo_lo_decidido_hasta_ese_momento() -> None:
    corte = datetime(2026, 9, 24, 10, 0, tzinfo=UTC)
    vieja = DecisionOperadorDto("MarcarPendiente", actualizado_en=corte)
    despues = datetime(2026, 9, 24, 10, 5, tzinfo=UTC)
    nueva = DecisionOperadorDto("ForzarCascada", actualizado_en=despues)
    decisiones = {(1, "10"): vieja, (2, "10"): nueva}

    assert decisiones_no_descartadas(decisiones, corte) == {(2, "10"): nueva}
    assert decisiones_no_descartadas(decisiones, None) == decisiones


def test_descartar_hasta_sin_zona_horaria_se_toma_como_utc() -> None:
    guardada = datetime(2026, 9, 24, 10, 5, tzinfo=UTC)
    decisiones = {(1, "10"): DecisionOperadorDto("ForzarCascada", actualizado_en=guardada)}

    assert decisiones_no_descartadas(decisiones, datetime(2026, 9, 24, 10, 0)) == decisiones
    assert decisiones_no_descartadas(decisiones, datetime(2026, 9, 24, 10, 5)) == {}


def test_decision_no_descartada_de_una_sola_fila() -> None:
    """El panel y las acciones usan el mismo corte que el tablero: tras
    "Descartar y empezar limpio" la fila efectiva vuelve al automático
    (`_overrides.Clear()` del legacy)."""
    corte = datetime(2026, 9, 24, 10, 0, tzinfo=UTC)
    vieja = DecisionOperadorDto("ForzarEntreReales", actualizado_en=corte)
    nueva = replace(vieja, actualizado_en=datetime(2026, 9, 24, 10, 1, tzinfo=UTC))

    assert decision_no_descartada(vieja, corte) is False
    assert decision_no_descartada(nueva, corte) is True
    assert decision_no_descartada(vieja, None) is True
