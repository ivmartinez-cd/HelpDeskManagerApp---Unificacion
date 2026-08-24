from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetIncidentesTecnicoRequest:
    periodo: int
    id_tecnico: int


@dataclass(frozen=True, slots=True)
class IncidenteBonoDTO:
    id_incidente: int
    categoria: str
    cliente: str
    sucursal: str
    nro_serie: str
