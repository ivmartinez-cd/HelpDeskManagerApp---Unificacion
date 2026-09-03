"""Conciliación de alertas entre re-análisis.

El motor regenera el set completo de alertas en cada corrida
(`replace_for_liquidacion` borra y crea). Sin conciliación, el triage de la TL
(resolver/descartar con justificación) se perdería en cada "Re-analizar". Regla:

- La alerta equivalente — misma clave `(incidente_id, tipo_alerta)`, única por
  diseño (una `Alerta` es 1:1 con (incidente, regla)) — conserva `estado` y
  `justificacion` si la TL ya la trabajó (estado ≠ pendiente).
- Una alerta que el motor ya no genera desaparece aunque estuviera descartada:
  el dato que la causaba se corrigió, así que la decisión quedó obsoleta.
"""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from src.modules.liquidaciones.domain.entities.alerta import ESTADO_PENDIENTE, Alerta
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import AlertaGenerada


@dataclass(frozen=True)
class AlertaConciliada:
    """Alerta del motor + la decisión previa de la TL que sobrevive al re-análisis."""

    generada: AlertaGenerada
    estado: str
    justificacion: str | None
    incidente_relacionado_id: uuid.UUID | None = None


def conciliar_alertas(
    existentes: list[Alerta], nuevas: Sequence[AlertaGenerada]
) -> list[AlertaConciliada]:
    trabajadas = {
        (a.incidente_id, a.tipo_alerta): a
        for a in existentes
        if a.estado != ESTADO_PENDIENTE
    }
    conciliadas = []
    for nueva in nuevas:
        previa = trabajadas.get((nueva.incidente_id, nueva.tipo_alerta))
        conciliadas.append(AlertaConciliada(
            generada=nueva,
            estado=previa.estado if previa else ESTADO_PENDIENTE,
            justificacion=previa.justificacion if previa else None,
            incidente_relacionado_id=previa.incidente_relacionado_id if previa else None,
        ))
    return conciliadas
