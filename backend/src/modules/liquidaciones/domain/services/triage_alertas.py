"""Recalcula `estado_validacion` de un incidente después de que la TL triage
sus alertas — la corrida original del motor (`motor.py::_evaluar_incidentes`)
solo fija "con_alertas"/"ok" al generar; esto lo actualiza cuando la TL termina
de revisar (resuelta) o descarta cada alerta, o reabre una ya cerrada."""

from collections.abc import Sequence

from src.modules.liquidaciones.domain.entities.alerta import ESTADO_DESCARTADA, ESTADO_RESUELTA
from src.modules.liquidaciones.domain.entities.incidente import (
    ESTADO_VALIDACION_CON_ALERTAS,
    ESTADO_VALIDACION_OK,
)

_ESTADOS_CERRADOS = frozenset({ESTADO_RESUELTA, ESTADO_DESCARTADA})


def recalcular_estado_incidente(estados_alertas: Sequence[str]) -> str:
    """OK si la TL ya resolvió o descartó TODAS las alertas del incidente;
    con_alertas si queda alguna pendiente o en revisión (incluye el caso de
    "Reabrir", que vuelve a dejar una alerta en en_revision)."""
    if estados_alertas and all(e in _ESTADOS_CERRADOS for e in estados_alertas):
        return ESTADO_VALIDACION_OK
    return ESTADO_VALIDACION_CON_ALERTAS
