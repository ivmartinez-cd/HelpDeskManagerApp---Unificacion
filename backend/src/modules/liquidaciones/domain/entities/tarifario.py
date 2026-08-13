"""Tarifario vigente por prestador/tipo de servicio/zona — tarifarios.

`zona=None` aplica a toda la zona del PST; un valor concreto (ej. "Villa Mercedes",
"Gral Roca") es una excepción de zona dentro del mismo prestador (caso INFOMAC). La
resolución real (match por tipo+zona+vigencia, con fallback a la fila sin zona) vive en
el motor de reglas (ALT001/ALT008), no acá — esta entidad es solo la fila de la tabla.
"""

import uuid
from dataclasses import dataclass
from datetime import date, datetime

TIPO_CORRECTIVO = "correctivo"
TIPO_PREVENTIVO = "preventivo"
TIPO_INSTALACION_DESINSTALACION = "instalacion_desinstalacion"
TIPO_PRE_CORRECTIVO = "pre_correctivo"
TIPO_GUARDIA = "guardia"
TIPO_SISTEMAS = "sistemas"

# Whitelist para descartar filas de texto libre que `normalizar_tipo_servicio`
# no logra mapear (ej. una fila de "TOTAL GENERAL" de un pie de tabla) — ver
# domain/services/importacion_maestro/tarifarios.py.
TIPOS_SERVICIO: tuple[str, ...] = (
    TIPO_CORRECTIVO,
    TIPO_PREVENTIVO,
    TIPO_INSTALACION_DESINSTALACION,
    TIPO_PRE_CORRECTIVO,
    TIPO_GUARDIA,
    TIPO_SISTEMAS,
)


@dataclass(frozen=True)
class Tarifario:
    id: uuid.UUID
    prestador_id: uuid.UUID
    tipo_servicio: str
    zona: str | None
    costo_servicio: float
    costo_km: float
    vigencia_desde: date
    vigencia_hasta: date | None
    created_at: datetime
