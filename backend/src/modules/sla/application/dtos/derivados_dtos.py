from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class IncidenteDerivadoDTO:
    id_incidente: int
    fecha_ingreso: datetime | None
    tipo: str
    estado: str
    cliente: str
    sucursal: str
    nro_serie: str
    modelo: str
    tecnico: str
    id_tecnico: int
    operador: str | None
    dias_desde_ingreso: int
    demorado: bool
