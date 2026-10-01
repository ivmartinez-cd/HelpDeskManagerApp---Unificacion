"""Acciones del operador sobre una fila del tablero de Proyección — los
handlers de `GrillaEstimacion` del legacy (`HandleAceptarSugerencia`,
`HandleMarcarPendiente`, `HandleUsarCascada`/`HandleUsarEntreReales`,
`HandleAceptarPL`). Cada una opera sobre la fila efectiva que la grilla
muestra (`fila_vigente.py`), guarda la decisión DEL PROCESO (se
restaura al volver a cargar el tablero, releyendo P/L y métodos con los
datos del día) y deja su entrada en la auditoría. La observación escrita va
solo a la auditoría, como el legacy. Los endpoints viven en
`presentation/proyeccion_candidatos_router.py`, que pasa la nota del operador ya limpia."""

from dataclasses import dataclass, replace

from src.modules.contadores.application.dtos.decision_operador_dto import (
    AccionDecision,
    ClaveDecisionDto,
    DecisionOperadorDto,
    ParPartidaLlegadaDto,
)
from src.modules.contadores.application.dtos.forzar_metodo_request import (
    ForzarMetodoRequest,
    MetodoForzado,
)
from src.modules.contadores.application.use_cases._resolver_resultado_final import (
    contador_anterior_de,
    resultado_pendiente_por_operador,
)
from src.modules.contadores.application.use_cases.forzar_metodo_candidato import forzar_metodo
from src.modules.contadores.application.use_cases.proyeccion_operador.auditoria import (
    RegistroAccion,
    detalle_pl,
    registrar_accion,
)
from src.modules.contadores.application.use_cases.proyeccion_operador.dependencias import (
    DependenciasProyeccion,
    OperadorProyeccion,
)
from src.modules.contadores.application.use_cases.proyeccion_operador.fila_vigente import (
    FilaVigente,
    fila_vigente,
    par_de_siges,
)
from src.modules.contadores.application.use_cases.proyeccion_operador.solicitud_real import (
    SeleccionProceso,
    clave_decision_de,
    entrada_de,
)
from src.modules.contadores.application.use_cases.recalcular_candidato import (
    lecturas_usables,
    pl_aceptable,
    recalcular_pl,
)
from src.modules.contadores.domain.errors import (
    AccionProyeccionInvalidaError,
    FilaProyeccionInexistenteError,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)

PL_INVALIDA = "Pareja Partida/Llegada inválida (separación < 15 días o L < P)"
PL_NO_USABLE = "La Partida y la Llegada tienen que ser lecturas elegibles (no estimados T14/T19)"
_PL_NO_ACEPTABLE = "Para aceptar la P/L hacen falta 15 días o más y la Llegada mayor que la Partida"
_SIN_SUGERENCIA = "La fila no tiene una sugerencia para aceptar"
_ACCION_FORZADA: dict[MetodoForzado, AccionDecision] = {
    "cascada_parque": "ForzarCascada",
    "entre_reales": "ForzarEntreReales",
}
# Observación fija que el legacy graba al forzar (`HandleUsarCascada` /
# `HandleUsarEntreReales`).
_OBSERVACION_FORZADA: dict[MetodoForzado, str] = {
    "cascada_parque": "Operador forzó estimación por cascada (T19).",
    "entre_reales": "Operador forzó estimación entre reales.",
}


@dataclass(frozen=True, slots=True)
class FilaAccion:
    """La fila sobre la que actúa el operador y la selección del proceso.
    `operador` elige la grilla que cargó ese usuario (su user id)."""

    id_maquina: int
    clase: str
    seleccion: SeleccionProceso
    operador: str | None = None

    @property
    def clave(self) -> ClaveDecisionDto:
        return clave_decision_de(self.id_maquina, self.clase, self.seleccion.nro_proceso)


async def entrada_o_404(fila: FilaAccion, deps: DependenciasProyeccion) -> EstimacionInput:
    entrada = await entrada_de(fila.id_maquina, fila.clase, fila.seleccion, deps, fila.operador)
    if entrada is None:
        raise FilaProyeccionInexistenteError()
    return entrada


async def vigente_o_404(fila: FilaAccion, deps: DependenciasProyeccion) -> FilaVigente:
    """`_panelEquipo = EquipoEfectivo(e)`: sin la fila no hay panel ni
    acción (el legacy siempre actúa sobre una fila de la grilla cargada)."""
    vigente = await fila_vigente(fila.id_maquina, fila.clase, fila.seleccion, deps, fila.operador)
    if vigente is None:
        raise FilaProyeccionInexistenteError()
    return vigente


async def aceptar_sugerencia(
    fila: FilaAccion, operador: OperadorProyeccion, deps: DependenciasProyeccion
) -> None:
    """`HandleAceptarSugerencia`: audita lo que la fila mostraba, con
    `Observacion = null` (el texto escrito en el panel se descarta, igual
    que en v1.7, y no llega a la OBSERVACION del CSV). Una decisión anterior
    deja de restaurarse. `PanelCandidatos` solo ofrece el botón si la fila
    tiene valor propuesto: sin él, 422."""
    vigente = await vigente_o_404(fila, deps)
    if vigente.resultado.estim_propuesto is None:
        raise AccionProyeccionInvalidaError(_SIN_SUGERENCIA)
    decision = DecisionOperadorDto("AceptarSugerencia")
    await deps.decisiones(fila.seleccion.nro_proceso).guardar(fila.clave, decision)
    registro = _registro(fila, "AceptarSugerencia", None, vigente)
    await registrar_accion(deps.estim_log, operador, registro)


async def marcar_pendiente(
    fila: FilaAccion, nota: str | None, operador: OperadorProyeccion, deps: DependenciasProyeccion
) -> None:
    """`HandleMarcarPendiente`: la fila en blanco y en rojo; se audita como
    no aceptada, con el propuesto igual al anterior y la observación."""
    vigente = await vigente_o_404(fila, deps)
    await deps.decisiones(fila.seleccion.nro_proceso).guardar(
        fila.clave, DecisionOperadorDto("MarcarPendiente")
    )
    pendiente = FilaVigente(vigente.entrada, resultado_pendiente_por_operador(vigente.resultado))
    registro = _registro(fila, "MarcarPendiente", nota, pendiente)
    no_aceptado = replace(registro, aceptado=False, contador_propuesto=registro.contador_anterior)
    await registrar_accion(deps.estim_log, operador, no_aceptado)


async def forzar(
    request: ForzarMetodoRequest, operador: OperadorProyeccion, deps: DependenciasProyeccion
) -> EstimacionResultado:
    """Botones "Usar T19 (cascada)" / "Usar entre reales": se aplica al toque y se
    guarda el MÉTODO (no el valor). 422 si el legacy no ofrece ese botón para
    la fila efectiva."""
    fila = FilaAccion(request.id_maquina, request.clase, request, str(operador.user_id))
    vigente = await vigente_o_404(fila, deps)
    forzado = forzar_metodo(request.metodo, vigente.entrada, vigente.resultado)
    if forzado is None:
        raise AccionProyeccionInvalidaError("Ese método no está disponible para esta fila")
    accion = _ACCION_FORZADA[request.metodo]
    await deps.decisiones(request.nro_proceso).guardar(fila.clave, DecisionOperadorDto(accion))
    observacion = _OBSERVACION_FORZADA[request.metodo]
    registro = _registro(fila, accion, observacion, FilaVigente(vigente.entrada, forzado))
    await registrar_accion(deps.estim_log, operador, registro)
    return forzado


async def aceptar_pl(
    fila: FilaAccion,
    par: ParPartidaLlegadaDto,
    nota: str | None,
    operador: OperadorProyeccion,
    deps: DependenciasProyeccion,
) -> None:
    """`HandleAceptarPL`: guarda la pareja (con sus `ID_Contador`, releída de
    Siges en el modo real) y audita la observación escrita; el valor se
    recalcula en cada carga del tablero."""
    par = await par_de_siges(par, fila.seleccion, deps)
    _validar_pl_aceptable(par)
    entrada = await entrada_o_404(fila, deps)
    resultado = recalcular_pl(par, entrada)
    if resultado is None:
        raise AccionProyeccionInvalidaError(PL_INVALIDA)
    decision = DecisionOperadorDto("PL_Manual", par.partida, par.llegada)
    await deps.decisiones(fila.seleccion.nro_proceso).guardar(fila.clave, decision)
    registro = _registro(fila, "PL_Manual", nota, FilaVigente(entrada, resultado))
    await registrar_accion(deps.estim_log, operador, replace(registro, detalle=detalle_pl(par)))


def validar_lecturas_usables(par: ParPartidaLlegadaDto) -> None:
    if not lecturas_usables(par):
        raise AccionProyeccionInvalidaError(PL_NO_USABLE)


def _validar_pl_aceptable(par: ParPartidaLlegadaDto) -> None:
    """Lo que `PanelCandidatos` exige para habilitar "Aceptar P/L manual"."""
    validar_lecturas_usables(par)
    if not pl_aceptable(par.partida, par.llegada):
        raise AccionProyeccionInvalidaError(_PL_NO_ACEPTABLE)


def _registro(
    fila: FilaAccion, accion: str, observacion: str | None, vigente: FilaVigente
) -> RegistroAccion:
    seleccion = fila.seleccion
    return RegistroAccion(
        fila.id_maquina,
        fila.clase,
        accion,
        seleccion.nro_proceso,
        seleccion.fecha_objetivo,
        observacion,
        resultado=vigente.resultado,
        contador_anterior=contador_anterior_de(vigente.entrada),
    )
