from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidenteDerivadoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
