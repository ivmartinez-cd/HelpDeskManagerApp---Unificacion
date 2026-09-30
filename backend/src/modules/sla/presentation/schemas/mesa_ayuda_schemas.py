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
    visita_id_incidente: int | None
    visita_tecnico: str | None
    visita_estado: str | None
    visitas_en_sucursal: int
