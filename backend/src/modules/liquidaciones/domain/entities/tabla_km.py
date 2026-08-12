"""Kilómetros esperados por par Empresa+Sucursal — tabla_kms.

`empresa_nombre`/`sucursal_nombre` son texto libre (no hay entidades Cliente/Sucursal
propias) — se resuelven por comparación case-insensitive contra `Incidente`, no por FK.
`umbral_viatico` es 30.0 por default pero configurable por excepción (ej. 20.0 para el
Aeropuerto de Santa Fe en PERTEX) — ver RN005 en `ANALISIS_FUNCIONAL...md` del legacy.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

UMBRAL_VIATICO_DEFAULT = 30.0


@dataclass(frozen=True)
class TablaKm:
    id: uuid.UUID
    prestador_id: uuid.UUID
    spst_id: uuid.UUID | None
    empresa_nombre: str
    sucursal_nombre: str
    observaciones: str | None
    domicilio_cliente: str | None
    localidad_cliente: str | None
    provincia_cliente: str | None
    kms_recorrido: float
    umbral_viatico: float
    aplica_viatico: bool
    kms_a_facturar: float
    url_maps: str | None
    created_at: datetime
    updated_at: datetime
