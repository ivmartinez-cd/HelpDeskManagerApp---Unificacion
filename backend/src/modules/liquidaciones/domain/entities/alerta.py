"""Alerta generada por el motor de reglas sobre un incidente puntual — alertas.

Un `Alerta` es 1:1 con la combinación (incidente, regla) — a diferencia de
`Observacion`, no agrupa varios incidentes. `tipo_alerta` es el código de
`ReglaAlerta.codigo`; ALT006/ALT007 son códigos válidos del catálogo pero sin
evaluador implementado (nunca se genera una `Alerta` con esos códigos hoy — ver
`LIQUIDACION_PRESTADORES_CARACTERIZACION.md` §3).
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

ESTADO_PENDIENTE = "pendiente"
ESTADO_EN_REVISION = "en_revision"
ESTADO_RESUELTA = "resuelta"
ESTADO_DESCARTADA = "descartada"


@dataclass(frozen=True)
class Alerta:
    id: uuid.UUID
    incidente_id: uuid.UUID
    liquidacion_id: uuid.UUID
    tipo_alerta: str
    descripcion: str | None
    datos_contexto: dict[str, Any] | None
    riesgo: float
    estado: str
    fecha_generacion: datetime
    # Motivo de la decisión de la TL — obligatorio al descartar; el re-análisis
    # lo preserva junto con el estado (ver `conciliar_alertas`).
    justificacion: str | None = None
