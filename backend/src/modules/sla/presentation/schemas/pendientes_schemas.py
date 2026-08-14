from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PrestadorPendientesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_tecnico: int
    tecnico: str
    cantidad: int
    ids_incidente: list[int]
    operador_nombre: str | None


class OperadorPendientesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    operador_nombre: str
    cantidad: int


class PendientesResumenResponse(BaseModel):
    """Resumen del backlog de incidentes sin cerrar — no es una colección
    paginada, es un objeto de agregado con `updated_at` de frescura."""

    model_config = ConfigDict(from_attributes=True)

    total: int
    por_prestador: list[PrestadorPendientesSchema]
    por_operador: list[OperadorPendientesSchema]
    updated_at: datetime


class IncidenteSinCerrarSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
