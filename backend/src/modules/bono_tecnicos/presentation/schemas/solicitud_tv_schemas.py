import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CrearSolicitudTvBody(BaseModel):
    """`id_tecnico`/`tecnico` no viajan acá: se resuelven del vínculo
    Empleado↔Siges del usuario autenticado (ver `CrearSolicitudTvPropia`)."""

    fecha: date
    razon_social: str = Field(min_length=1, max_length=200)
    sucursal: str = Field(min_length=1, max_length=200)
    tarea_realizada: str = Field(min_length=1, max_length=2000)


class DecisionSolicitudTvBody(BaseModel):
    decision: Literal["APROBADA", "RECHAZADA"]
    motivo: str | None = Field(default=None, max_length=500)


class SolicitudTvSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    id_tecnico: int
    tecnico: str
    periodo: int
    fecha: date
    razon_social: str
    sucursal: str
    tarea_realizada: str
    estado: str
    creado_en: datetime
    resuelta_en: datetime | None
    resuelta_por_email: str | None
    motivo_rechazo: str | None
