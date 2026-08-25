from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidenteMesaAyudaSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
