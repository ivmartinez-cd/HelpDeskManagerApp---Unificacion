"""Schemas de Tier 1 de geovalidación (reverse geocoding de Georef)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.use_cases.geovalidacion_tier1 import (
    HallazgoTier1,
    ResultadoConsultarGeoref,
)


class ResultadoConsultarGeorefOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    consultadas: int
    ya_en_cache: int = Field(serialization_alias="yaEnCache")
    sin_coordenadas: int = Field(serialization_alias="sinCoordenadas")
    pendientes_por_tope: int = Field(serialization_alias="pendientesPorTope")

    @classmethod
    def from_dto(cls, r: ResultadoConsultarGeoref) -> ResultadoConsultarGeorefOut:
        return cls(
            consultadas=r.consultadas,
            ya_en_cache=r.ya_en_cache,
            sin_coordenadas=r.sin_coordenadas,
            pendientes_por_tope=r.pendientes_por_tope,
        )


class HallazgoTier1Out(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    siges_sucursal_id: int = Field(serialization_alias="sigesSucursalId")
    empresa_nombre: str = Field(serialization_alias="empresaNombre")
    sucursal_nombre: str = Field(serialization_alias="sucursalNombre")
    provincia_declarada: str | None = Field(serialization_alias="provinciaDeclarada")
    provincia_georef: str = Field(serialization_alias="provinciaGeoref")
    latitud: float
    longitud: float

    @classmethod
    def from_dto(cls, h: HallazgoTier1) -> HallazgoTier1Out:
        return cls(
            siges_sucursal_id=h.siges_sucursal_id,
            empresa_nombre=h.empresa_nombre,
            sucursal_nombre=h.sucursal_nombre,
            provincia_declarada=h.provincia_declarada,
            provincia_georef=h.provincia_georef,
            latitud=h.latitud,
            longitud=h.longitud,
        )
