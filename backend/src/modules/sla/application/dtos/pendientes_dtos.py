from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PrestadorPendientesDTO:
    id_tecnico: int
    tecnico: str
    cantidad: int
    ids_incidente: list[int]
    operador_nombre: str | None


@dataclass(frozen=True, slots=True)
class OperadorPendientesDTO:
    operador_nombre: str
    cantidad: int


@dataclass(frozen=True, slots=True)
class PendientesResumenResult:
    total: int
    por_prestador: list[PrestadorPendientesDTO]
    por_operador: list[OperadorPendientesDTO]
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class IncidenteSinCerrarDTO:
    id_incidente: int
    tecnico: str
    id_tecnico: int
    cliente: str
    sucursal: str
    modelo: str
    nro_serie: str
    fecha_ingreso: datetime | None
    fecha_finalizacion: datetime | None
    dias_en_estado: int
