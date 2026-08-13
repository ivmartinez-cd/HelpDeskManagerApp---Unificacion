"""Value objects del SOAP de Canal Directo para liquidaciones."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class CdLiquidacion:
    id: int
    prestador_cd_id: int
    numero_liquidacion: str   # f"{id}-{id % 10}"
    fecha_liquidacion: date
    estado: str
    cant_incidentes: int


@dataclass(frozen=True)
class CdIncidenteRow:
    id: int
    tipo: str
    empresa_nombre: str
    sucursal_nombre: str
    nro_serie: str
    fecha_cierre: date | None
    costo_servicio: float
    cant_km: float
    costo_km: float
    rubro: str
    pasa_it: bool
