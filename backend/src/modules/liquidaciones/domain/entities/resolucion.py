"""Decisión de la Team Leader sobre una alerta — resoluciones."""

import uuid
from dataclasses import dataclass
from datetime import datetime

DECISION_APROBAR = "aprobar"
DECISION_SOLICITAR_CORRECCION = "solicitar_correccion"
DECISION_IGNORAR = "ignorar"
DECISION_ESCALAR = "escalar"


@dataclass(frozen=True)
class Resolucion:
    id: uuid.UUID
    alerta_id: uuid.UUID
    decision: str
    justificacion: str | None
    comentario: str | None
    fecha: datetime
