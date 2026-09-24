"""P/L manual del panel de candidatos (`RecalcularConPL` del legacy) sobre la
fila de un proceso, real o de ejemplo — quien llama arma el `EstimacionInput`
(`_proyeccion_solicitud_real.entrada_de`)."""

from src.modules.contadores.application.dtos.decision_operador_dto import (
    LecturaElegidaDto,
    ParPartidaLlegadaDto,
)
from src.modules.contadores.domain.ports.candidatos_equipo_port import LecturaCandidataSiges
from src.modules.contadores.domain.services.estimacion.motor import contexto_de
from src.modules.contadores.domain.services.estimacion.recalcular_manual import recalcular_con_pl
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)

# `PanelCandidatos.PLValida` del legacy (mismo umbral que `MinDiasSeparacion`).
_MIN_DIAS_PL = 15


def recalcular_pl(
    par: ParPartidaLlegadaDto, entrada: EstimacionInput
) -> EstimacionResultado | None:
    """`None` = pareja inválida (menos de 15 días o Llegada menor que
    Partida): el legacy no muestra vista previa ni cambia la fila."""
    return recalcular_con_pl(
        contexto_de(entrada), par.partida.a_lectura_ref(), par.llegada.a_lectura_ref()
    )


def lecturas_usables(par: ParPartidaLlegadaDto) -> bool:
    """El panel del legacy solo deja marcar como P o L las lecturas
    `EsUsableComoCandidate` (real, T4, inicial/final, web cliente): un
    estimado T14/T19 nunca entra en una P/L."""
    return _usable(par.partida) and _usable(par.llegada)


def pl_aceptable(partida: LecturaElegidaDto, llegada: LecturaElegidaDto) -> bool:
    """`PanelCandidatos.PLValida`: el legacy solo habilita "Aceptar P/L
    manual" con al menos 15 días calendario entre Partida y Llegada y la
    Llegada MAYOR que la Partida (más estricto que `RecalcularConPL`, que
    acepta Δ=0 para la vista previa)."""
    dias = (llegada.fecha - partida.fecha).days
    return dias >= _MIN_DIAS_PL and llegada.valor > partida.valor


def _usable(lectura: LecturaElegidaDto) -> bool:
    candidata = LecturaCandidataSiges(
        id_contador=lectura.id_contador or 0,
        fecha=lectura.fecha,
        tipo_toma=lectura.tipo_toma,
        valor=lectura.valor,
        para_facturar=lectura.para_facturar,
    )
    return candidata.usable
