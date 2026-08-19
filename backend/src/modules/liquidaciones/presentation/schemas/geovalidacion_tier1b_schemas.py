"""Schemas de Tier 1b de geovalidación (segunda opinión de Nominatim)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.use_cases.geovalidacion_tier1b import (
    HallazgoTier1b,
    ResultadoConsultarNominatim,
)
from src.modules.liquidaciones.domain.repositories.nominatim_gateway import ATRIBUCION_ODBL


class ResultadoConsultarNominatimOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    consultadas: int
    ya_en_cache: int = Field(serialization_alias="yaEnCache")
    pendientes_por_tope: int = Field(serialization_alias="pendientesPorTope")

    @classmethod
    def from_dto(cls, r: ResultadoConsultarNominatim) -> ResultadoConsultarNominatimOut:
        return cls(
            consultadas=r.consultadas,
            ya_en_cache=r.ya_en_cache,
            pendientes_por_tope=r.pendientes_por_tope,
        )


class HallazgoTier1bOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    siges_sucursal_id: int = Field(serialization_alias="sigesSucursalId")
    empresa_nombre: str = Field(serialization_alias="empresaNombre")
    sucursal_nombre: str = Field(serialization_alias="sucursalNombre")
    provincia_declarada: str | None = Field(serialization_alias="provinciaDeclarada")
    provincia_georef: str = Field(serialization_alias="provinciaGeoref")
    provincia_nominatim: str = Field(serialization_alias="provinciaNominatim")
    latitud: float
    longitud: float
    atribucion: str = ATRIBUCION_ODBL

    @classmethod
    def from_dto(cls, h: HallazgoTier1b) -> HallazgoTier1bOut:
        return cls(
            siges_sucursal_id=h.siges_sucursal_id,
            empresa_nombre=h.empresa_nombre,
            sucursal_nombre=h.sucursal_nombre,
            provincia_declarada=h.provincia_declarada,
            provincia_georef=h.provincia_georef,
            provincia_nominatim=h.provincia_nominatim,
            latitud=h.latitud,
            longitud=h.longitud,
        )
