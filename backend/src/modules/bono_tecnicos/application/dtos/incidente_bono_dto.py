import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class GetIncidentesTecnicoRequest:
    periodo: int
    id_tecnico: int


@dataclass(frozen=True, slots=True)
class GetMisIncidentesRequest:
    user_id: uuid.UUID
    periodo: int


@dataclass(frozen=True, slots=True)
class IncidenteBonoDTO:
    id_incidente: int
    categoria: str
    cliente: str
    sucursal: str
    nro_serie: str
    fecha_cierre: datetime | None
