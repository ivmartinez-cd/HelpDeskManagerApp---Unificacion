import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.modules.reportes_app.infrastructure.repositories.sqlalchemy_reporte_app_repository import (  # noqa: E501
    ReporteVista,
)


class ReporteOut(BaseModel):
    id: uuid.UUID
    tipo: str
    estado: str
    ruta: str
    detalle: str
    tiene_foto: bool
    nota: str | None
    respuesta: str | None
    usuario: str | None
    creado_en: datetime
    actualizado_en: datetime | None

    @classmethod
    def from_vista(cls, v: ReporteVista) -> "ReporteOut":
        return cls.model_validate(v, from_attributes=True)


class DecisionIn(BaseModel):
    """`pedir_cambios` devuelve el reporte a `nuevo` para que Claude rehaga la
    propuesta teniendo en cuenta `respuesta`, que en ese caso es obligatoria."""

    decision: Literal["aprobar", "pedir_cambios", "descartar"]
    respuesta: str | None = Field(default=None, max_length=5000)
