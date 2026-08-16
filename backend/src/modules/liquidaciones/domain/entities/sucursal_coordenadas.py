"""Resolución de coordenadas de una sucursal cliente SIN coords en Siges.

Siges es de solo lectura para este módulo: cuando una sucursal no tiene pin
cargado allá, la coordenada elegida (geocode confirmado o carga manual) vive
acá. El geocode nunca pisa una coordenada existente: estas filas solo llenan
vacíos, y el estado se deriva — resuelta si hay lat/lon; si no, ambigua o sin
resultados según los candidatos cacheados para su dirección."""

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SucursalCoordenadas:
    id: uuid.UUID
    prestador_id: uuid.UUID
    siges_sucursal_id: int
    empresa_nombre: str
    sucursal_nombre: str
    direccion_normalizada: str | None
    latitud: float | None
    longitud: float | None
    procedencia: str | None
    formatted_address: str | None
    fecha_resolucion: datetime | None
    created_at: datetime
    updated_at: datetime

    @property
    def resuelta(self) -> bool:
        return self.latitud is not None and self.longitud is not None
