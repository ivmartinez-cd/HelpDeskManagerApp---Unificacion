from pydantic import BaseModel, ConfigDict


class IncidenteBonoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_incidente: int
    categoria: str
    cliente: str
    sucursal: str
    nro_serie: str
