"""Tarifario vigente por prestador/tipo de servicio/SPST — tarifarios.

`spst_id=None` es la tarifa genérica del prestador (aplica a cualquier SPST sin
tarifa propia); un `spst_id` concreto es una excepción puntual de ese SPST
dentro del mismo prestador (caso INFOMAC — cada base tiene su propio costo).
Hasta 2026-09 esto era un campo `zona` de texto libre que tenía que matchear
letra por letra con `Spst.zona_cobertura`; se reemplazó por esta FK porque,
verificado contra la base real, ninguna "zona" fue nunca compartida por más de
un SPST del mismo prestador — la zona siempre fue un alias 1:1 de un SPST. La
resolución real (match por tipo+spst_id+vigencia, con fallback a la fila sin
spst_id) vive en el motor de reglas (ALT001/ALT008), no acá — esta entidad es
solo la fila de la tabla.
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
    spst_id: uuid.UUID | None
    costo_servicio: float
    costo_km: float
    vigencia_desde: date
    vigencia_hasta: date | None
    created_at: datetime
