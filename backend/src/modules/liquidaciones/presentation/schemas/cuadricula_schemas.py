"""Schemas del mapeo cuadrícula-Siges → sucursal-base del PST."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.use_cases.siges_cuadriculas import CuadriculaConMapeo
from src.modules.liquidaciones.domain.entities.cuadricula_base_map import CuadriculaBaseMap


class CuadriculaOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    cuadricula: str
    siges_base_sucursal_id: int | None = Field(
        serialization_alias="sigesBaseSucursalId"
    )

    @classmethod
    def from_dto(cls, dto: CuadriculaConMapeo) -> CuadriculaOut:
        return cls(
            cuadricula=dto.cuadricula,
            siges_base_sucursal_id=dto.siges_base_sucursal_id,
        )


class MapearCuadriculaIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    siges_base_sucursal_id: int = Field(alias="sigesBaseSucursalId")


class CuadriculaMapOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: uuid.UUID
    prestador_id: uuid.UUID = Field(serialization_alias="prestadorId")
    cuadricula: str
    siges_base_sucursal_id: int = Field(serialization_alias="sigesBaseSucursalId")

    @classmethod
    def from_entity(cls, e: CuadriculaBaseMap) -> CuadriculaMapOut:
        return cls(
            id=e.id,
            prestador_id=e.prestador_id,
            cuadricula=e.cuadricula,
            siges_base_sucursal_id=e.siges_base_sucursal_id,
        )
