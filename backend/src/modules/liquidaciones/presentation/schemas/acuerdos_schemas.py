"""Schemas de acuerdos de precio por cliente (/api/liquidaciones/acuerdos)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.use_cases.config_acuerdos import AcuerdoDatos
from src.modules.liquidaciones.domain.entities.acuerdo_precio_cliente import (
    AcuerdoPrecioCliente,
)


class AcuerdoIn(BaseModel):
    """Exactamente uno de `factor` / `precioFijo` (lo valida el caso de uso)."""

    model_config = ConfigDict(populate_by_name=True)
    prestador_id: uuid.UUID = Field(alias="prestadorId")
    empresa_nombre: str = Field(alias="empresaNombre", min_length=1)
    tipo_servicio: str | None = Field(default=None, alias="tipoServicio")
    factor: float | None = None
    precio_fijo: float | None = Field(default=None, alias="precioFijo")
    motivo: str = Field(min_length=1)
    vigencia_desde: date = Field(alias="vigenciaDesde")
    vigencia_hasta: date | None = Field(default=None, alias="vigenciaHasta")

    def to_datos(self) -> AcuerdoDatos:
        return AcuerdoDatos(
            empresa_nombre=self.empresa_nombre,
            tipo_servicio=self.tipo_servicio or None,
            factor=self.factor,
            precio_fijo=self.precio_fijo,
            motivo=self.motivo,
            vigencia_desde=self.vigencia_desde,
            vigencia_hasta=self.vigencia_hasta,
        )


class AcuerdoOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: uuid.UUID
    prestador_id: uuid.UUID = Field(serialization_alias="prestadorId")
    empresa_nombre: str = Field(serialization_alias="empresaNombre")
    tipo_servicio: str | None = Field(serialization_alias="tipoServicio")
    factor: float | None
    precio_fijo: float | None = Field(serialization_alias="precioFijo")
    motivo: str
    vigencia_desde: date = Field(serialization_alias="vigenciaDesde")
    vigencia_hasta: date | None = Field(serialization_alias="vigenciaHasta")
    created_at: datetime = Field(serialization_alias="createdAt")

    @classmethod
    def from_entity(cls, e: AcuerdoPrecioCliente) -> AcuerdoOut:
        return cls(
            id=e.id,
            prestador_id=e.prestador_id,
            empresa_nombre=e.empresa_nombre,
            tipo_servicio=e.tipo_servicio,
            factor=e.factor,
            precio_fijo=e.precio_fijo,
            motivo=e.motivo,
            vigencia_desde=e.vigencia_desde,
            vigencia_hasta=e.vigencia_hasta,
            created_at=e.created_at,
        )
