"""Schemas de las acciones sobre Tabla KM que nacen en el detalle de la
liquidación (zona de la sucursal, km de referencia) y del archivado."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class AsignarZonaSucursalIn(BaseModel):
    """`spstId` null = zona Genérica (tarifario sin SPST)."""

    model_config = ConfigDict(populate_by_name=True)
    prestador_id: uuid.UUID = Field(alias="prestadorId")
    empresa_nombre: str = Field(alias="empresaNombre", min_length=1)
    sucursal_nombre: str = Field(alias="sucursalNombre", min_length=1)
    spst_id: uuid.UUID | None = Field(default=None, alias="spstId")


class KmReferenciaIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    prestador_id: uuid.UUID = Field(alias="prestadorId")
    empresa_nombre: str = Field(alias="empresaNombre", min_length=1)
    sucursal_nombre: str = Field(alias="sucursalNombre", min_length=1)
    kms: float = Field(gt=0)


class ArchivadaIn(BaseModel):
    archivada: bool
