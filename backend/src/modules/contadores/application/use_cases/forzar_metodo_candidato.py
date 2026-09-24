"""Botones "Usar T19 (cascada)" / "Usar entre reales" del panel de candidatos
(`ForzarCascada` / `ForzarEntreReales` del legacy) sobre la fila de un
proceso, real o de ejemplo."""

from src.modules.contadores.application.dtos.forzar_metodo_request import MetodoForzado
from src.modules.contadores.application.use_cases._resolver_resultado_final import (
    es_fuente_pendiente,
)
from src.modules.contadores.domain.services.estimacion.forzar_metodo import (
    forzar_cascada_parque,
    forzar_entre_reales,
)
from src.modules.contadores.domain.services.estimacion.motor import contexto_de
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)

# `GrillaEstimacion.EsFuenteParque` del legacy.
_FUENTES_PARQUE = frozenset(
    {"Parque_Cliente_Tec", "Parque_Cliente_Modelo", "Parque_Grupo_Modelo", "Parque_Global_Modelo"}
)


def forzar_metodo(
    metodo: MetodoForzado, entrada: EstimacionInput, vigente: EstimacionResultado
) -> EstimacionResultado | None:
    """La alternativa se calcula sobre la fila original (no sobre la decisión
    que tenga) y se ofrece según lo que la fila muestra hoy (`vigente`), como
    `PuedeUsarCascada` / `PuedeUsarEntreReales`. `None` = el legacy no ofrece
    ese botón: cascada sin parque (quedaría pendiente) o la fila ya sale de un
    parque; entre reales sin par válido o la fila ya es historia propia."""
    ctx = contexto_de(entrada)
    if metodo == "entre_reales":
        forzado = forzar_entre_reales(ctx)
        return forzado if vigente.fuente != "Historia_Propia" else None
    cascada = forzar_cascada_parque(ctx)
    if es_fuente_pendiente(cascada.fuente) or vigente.fuente in _FUENTES_PARQUE:
        return None
    return cascada
