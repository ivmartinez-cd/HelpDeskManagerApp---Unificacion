import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SucursalParaGeocoding:
    """Una sucursal del universo de preventivos (independiente de zona) con
    lo necesario para armar la dirección a geocodificar. `latitud`/`longitud`
    son las de Siges tal cual (posiblemente inválidas — para eso existe esta
    entidad); su validación es responsabilidad de domain/services/coordenadas.py."""

    id_sucursal: int
    cliente: str
    sucursal: str
    domicilio: str
    ciudad: str
    provincia: str
    latitud: float | None
    longitud: float | None


@dataclass(frozen=True, slots=True)
class SucursalCoordenadas:
    """Coordenada resuelta para una sucursal sin pin usable en Siges (Siges
    es de solo lectura para este módulo). Solo existen filas para sucursales
    efectivamente resueltas — ambiguas/sin resultado no se persisten, quedan
    "sin ubicar" y se reintentan (gratis, vía cache) en la próxima corrida.

    `corregido_por_user_id`/`corregido_por_nombre`/`nota` son `None` cuando la
    fila viene de geocoding automático (comportamiento original, sin cambios)
    y se completan cuando un operador la corrige a mano desde la UI —
    `corregido_por_user_id IS NOT NULL` es el discriminador, no hace falta un
    campo `origen` separado. `corregido_por_nombre` es snapshot del nombre al
    momento de corregir (mismo criterio que `HabilitacionPreventivo`)."""

    siges_sucursal_id: int
    latitud: float
    longitud: float
    formatted_address: str
    fecha_resolucion: datetime
    corregido_por_user_id: uuid.UUID | None = None
    corregido_por_nombre: str | None = None
    nota: str | None = None


@dataclass(frozen=True, slots=True)
class GeocodificarResultado:
    resueltas: int
    ambiguas: int
    sin_resultados: int
    sin_direccion: int
    reconciliadas: int
