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
    visita_id_incidente: int | None = None
    visita_tecnico: str | None = None
    visita_estado: str | None = None
    visitas_en_sucursal: int = 0
