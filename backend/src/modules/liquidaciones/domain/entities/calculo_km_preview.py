"""Propuesta persistida del cálculo masivo de distancias (two-step).

El preview guarda TODO lo que el apply necesita: aplicar no vuelve a llamar a
Google ni a Siges — solo materializa filas ya calculadas y confirmadas por el
usuario. `kms_recorrido`/`kms_a_facturar` siguen la convención de negocio
confirmada en Fase 0 (2026-08-15): total ida+vuelta, para todos los
prestadores."""

import uuid
from dataclasses import dataclass
from datetime import datetime

ACCION_CREAR = "crear"
ACCION_ACTUALIZAR = "actualizar"


@dataclass(frozen=True)
class PreviewFila:
    accion: str
    tabla_km_id: uuid.UUID | None
    siges_sucursal_id: int | None
    empresa_nombre: str
    sucursal_nombre: str
    domicilio: str | None
    localidad: str | None
    provincia: str | None
    coords_origen: str
    latitud_destino: float
    longitud_destino: float
    latitud_base: float
    longitud_base: float
    kms_ida: float
    kms_vuelta: float
    kms_total: float
    umbral_viatico: float
    aplica_viatico: bool
    kms_a_facturar: float
    kms_recorrido_actual: float | None
    kms_a_facturar_actual: float | None
    id_costo_servicios: int | None = None


@dataclass(frozen=True)
class CalculoKmPreview:
    id: uuid.UUID
    prestador_id: uuid.UUID
    filas: tuple[PreviewFila, ...]
    sin_ubicar: int
    sin_ruta: int
    elementos_google: int
    created_at: datetime
