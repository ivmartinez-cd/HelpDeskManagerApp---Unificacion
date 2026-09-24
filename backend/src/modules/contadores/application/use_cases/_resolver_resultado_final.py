"""Resultado final de una fila (equipo, clase) — el cálculo automático del motor
salvo que el operador haya tomado una decisión sobre esa fila en ESE proceso.
Lo comparten el tablero (`get_tablero_proyeccion.py`) y el export a SiGes,
para que ambos muestren siempre lo mismo.

Mismo criterio que el legacy al restaurar el trabajo de una sesión anterior
(`GrillaEstimacion.RestaurarOverridesAsync` / `ReconstruirOverrideAsync`):

- "Aceptar sugerencia" no se restaura: la fila queda en el automático.
- Fila que ya tiene lectura real: la decisión cuenta como descartada y se
  muestra la real (un dato real nunca se pisa).
- "Marcar pendiente": la fila en blanco y en rojo (`ConstruirPendiente`).
- Forzar cascada / entre reales: se vuelve a correr ESE método con los datos
  del día (no un valor congelado); entre reales que ya no aplica, descartada.
- P/L manual: se recalcula con la Partida/Llegada guardadas (el tablero las
  relee de Siges por `ID_Contador`); pareja inválida o lectura que ya no
  está, descartada.

La observación que escribe el operador no forma parte de la decisión: el
legacy solo la graba en la auditoría (`Estim_Log.Observacion`)."""

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Literal

from src.modules.contadores.application.dtos.decision_operador_dto import DecisionOperadorDto
from src.modules.contadores.domain.services.estimacion.forzar_metodo import (
    forzar_cascada_parque,
    forzar_entre_reales,
)
from src.modules.contadores.domain.services.estimacion.motor import contexto_de, estimar
from src.modules.contadores.domain.services.estimacion.recalcular_manual import recalcular_con_pl
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
)

EstadoDecision = Literal["ninguna", "restaurada", "descartada"]

# El motor representa `RequierePendiente` del legacy con esta fuente.
FUENTE_PENDIENTE: FuenteEstimacion = "Pendiente"


@dataclass(frozen=True, slots=True)
class FilaResuelta:
    """`estado_decision` alimenta el banner "Restauramos N decisiones… / M
    descartadas" y la marca "editado" de la grilla."""

    resultado: EstimacionResultado
    estado_decision: EstadoDecision = "ninguna"


def resolver_resultado_final(
    entrada: EstimacionInput, decision: DecisionOperadorDto | None
) -> FilaResuelta:
    automatico = estimar(entrada)
    restaurable = _decision_restaurable(decision)
    if restaurable is None:
        return FilaResuelta(automatico)
    if not entrada.pendiente_estimar:
        return FilaResuelta(automatico, "descartada")
    reconstruido = _reconstruir(restaurable, entrada, automatico)
    if reconstruido is None:
        return FilaResuelta(automatico, "descartada")
    return FilaResuelta(reconstruido, "restaurada")


def es_fuente_pendiente(fuente: str) -> bool:
    """Fila que quedó para completar a mano (`RequierePendiente` del legacy)."""
    return fuente == FUENTE_PENDIENTE


def decisiones_no_descartadas(
    decisiones: dict[tuple[int, str], DecisionOperadorDto], descartar_hasta: datetime | None
) -> dict[tuple[int, str], DecisionOperadorDto]:
    """Botón "Descartar y empezar limpio": sin efecto sobre lo guardado, solo
    deja afuera lo decidido hasta ese momento (ver `SolicitudRestauracionDto`)."""
    return {
        clave: decision
        for clave, decision in decisiones.items()
        if decision_no_descartada(decision, descartar_hasta)
    }


def decision_no_descartada(
    decision: DecisionOperadorDto, descartar_hasta: datetime | None
) -> bool:
    """Una sola fila: lo mismo que el tablero, para que el panel y las
    acciones vean la fila efectiva (`EquipoEfectivo`) que muestra la grilla
    después de "Descartar y empezar limpio" (`_overrides.Clear()`). Un
    `descartar_hasta` sin zona horaria se toma como UTC (lo guardado la tiene
    siempre)."""
    if descartar_hasta is None:
        return True
    if descartar_hasta.tzinfo is None:
        descartar_hasta = descartar_hasta.replace(tzinfo=UTC)
    return decision.actualizado_en is not None and decision.actualizado_en > descartar_hasta


def resultado_pendiente_por_operador(base: EstimacionResultado) -> EstimacionResultado:
    """`GrillaEstimacion.ConstruirPendiente`: conserva el resto del cálculo
    (composición del tooltip, meses sin real) y deja la fila sin valor, en
    rojo y sin la guía para el operador (`NotaOperador = null`)."""
    return replace(
        base,
        estim_propuesto=None,
        impresiones=None,
        tipo_toma=None,
        fuente=FUENTE_PENDIENTE,
        metodo_detalle="Marcado pendiente por el operador",
        requiere_confirmacion=False,
        semaforo="ROJO",
        borde_salto_imposible=False,
        t4_sin_revisar=False,
        coloreo="NORMAL",
        detalle_calculo="Marcado pendiente por operador.",
        nota_operador=None,
    )


def contador_anterior_de(entrada: EstimacionInput) -> float:
    """`ContadorAnterior_Valor ?? 0` con que el legacy audita cada acción."""
    anterior = entrada.ultimo_contador_facturado
    return anterior.valor if anterior is not None else 0.0


def _decision_restaurable(decision: DecisionOperadorDto | None) -> DecisionOperadorDto | None:
    if decision is None or decision.accion == "AceptarSugerencia":
        return None
    return decision


def _reconstruir(
    decision: DecisionOperadorDto, entrada: EstimacionInput, automatico: EstimacionResultado
) -> EstimacionResultado | None:
    if decision.accion == "MarcarPendiente":
        return resultado_pendiente_por_operador(automatico)
    ctx = contexto_de(entrada)
    if decision.accion == "ForzarCascada":
        return forzar_cascada_parque(ctx)
    if decision.accion == "ForzarEntreReales":
        return forzar_entre_reales(ctx)
    if decision.partida is None or decision.llegada is None:
        return None
    partida, llegada = decision.partida.a_lectura_ref(), decision.llegada.a_lectura_ref()
    return recalcular_con_pl(ctx, partida, llegada)
