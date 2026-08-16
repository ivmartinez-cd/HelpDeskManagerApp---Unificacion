"""Kilómetros esperados por par Empresa+Sucursal — tabla_kms.

`empresa_nombre`/`sucursal_nombre` son texto libre (no hay entidades Cliente/Sucursal
propias) — se resuelven por comparación case-insensitive contra `Incidente`, no por FK.
`umbral_viatico` es 30.0 por default pero configurable por excepción (ej. 20.0 para el
Aeropuerto de Santa Fe en PERTEX) — ver RN005 en `ANALISIS_FUNCIONAL...md` del legacy.

Convención de km (Fase 0, 2026-08-15, validada con datos reales): TODOS los prestadores
facturan ida y vuelta — `kms_recorrido` y `kms_a_facturar` son el TOTAL del viaje, y
`umbral_viatico` se compara contra ese total. `kms_ida`/`kms_vuelta` son los tramos
reales medidos por Google (la vuelta B→A puede diferir de la ida por manos únicas).
`coords_origen` registra la procedencia del pin destino ('siges' | 'geocode' | 'manual').
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
    latitud_destino: float | None = None
    longitud_destino: float | None = None
    kms_ida: float | None = None
    kms_vuelta: float | None = None
    coords_origen: str | None = None
    geocode_formatted_address: str | None = None
    geocode_fecha: datetime | None = None
