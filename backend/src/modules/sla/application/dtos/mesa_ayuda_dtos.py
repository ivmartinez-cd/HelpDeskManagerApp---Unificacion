from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class IncidenteMesaAyudaDTO:
    id_incidente: int
    fecha_ingreso: datetime | None
    tipo: str
    estado: str
    cliente: str
    sucursal: str
    nro_serie: str
    modelo: str
    operador_login: str
    operador: str
    dias_transcurridos: int
    demorado: bool
