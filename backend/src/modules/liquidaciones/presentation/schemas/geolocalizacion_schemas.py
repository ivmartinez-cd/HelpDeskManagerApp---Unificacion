"""Schemas de geocodificación, resolución de coordenadas y pines sospechosos."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.use_cases.geocodificar_sucursales import (
    GeocodificarResultado,
)
from src.modules.liquidaciones.application.use_cases.pines_sospechosos import (
    AuditarPinesResultado,
    PinSospechoso,
)
from src.modules.liquidaciones.application.use_cases.resolver_coordenadas import (
    SucursalConCandidatos,
)
from src.modules.liquidaciones.domain.repositories.geocoding_gateway import GeocodeCandidato


class GeocodeCandidatoOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    formatted_address: str = Field(serialization_alias="formattedAddress")
    latitud: float
    longitud: float
    location_type: str = Field(serialization_alias="locationType")
    tipos: list[str]
    partial_match: bool = Field(serialization_alias="partialMatch")

    @classmethod
    def from_entity(cls, c: GeocodeCandidato) -> GeocodeCandidatoOut:
        return cls(
            formatted_address=c.formatted_address,
            latitud=c.latitud,
            longitud=c.longitud,
            location_type=c.location_type,
            tipos=list(c.tipos),
            partial_match=c.partial_match,
        )


class GeocodificarResultadoOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    resueltas_auto: int = Field(serialization_alias="resueltasAuto")
    ambiguas: int
    sin_resultados: int = Field(serialization_alias="sinResultados")
    sin_direccion: int = Field(serialization_alias="sinDireccion")
    ya_resueltas: int = Field(serialization_alias="yaResueltas")
    llamadas_google: int = Field(serialization_alias="llamadasGoogle")
    pendientes_por_tope: int = Field(serialization_alias="pendientesPorTope")

    @classmethod
    def from_dto(cls, r: GeocodificarResultado) -> GeocodificarResultadoOut:
        return cls(
            resueltas_auto=r.resueltas_auto,
            ambiguas=r.ambiguas,
            sin_resultados=r.sin_resultados,
            sin_direccion=r.sin_direccion,
            ya_resueltas=r.ya_resueltas,
            llamadas_google=r.llamadas_google,
            pendientes_por_tope=r.pendientes_por_tope,
        )


class SucursalCoordenadasOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    siges_sucursal_id: int = Field(serialization_alias="sigesSucursalId")
    empresa_nombre: str = Field(serialization_alias="empresaNombre")
    sucursal_nombre: str = Field(serialization_alias="sucursalNombre")
    direccion: str | None
    estado: str
    latitud: float | None
    longitud: float | None
    procedencia: str | None
    formatted_address: str | None = Field(serialization_alias="formattedAddress")
    candidatos: list[GeocodeCandidatoOut]

    @classmethod
    def from_dto(cls, d: SucursalConCandidatos) -> SucursalCoordenadasOut:
        return cls(
            siges_sucursal_id=d.sucursal.siges_sucursal_id,
            empresa_nombre=d.sucursal.empresa_nombre,
            sucursal_nombre=d.sucursal.sucursal_nombre,
            direccion=d.sucursal.direccion_normalizada,
            estado=d.estado,
            latitud=d.sucursal.latitud,
            longitud=d.sucursal.longitud,
            procedencia=d.sucursal.procedencia,
            formatted_address=d.sucursal.formatted_address,
            candidatos=[GeocodeCandidatoOut.from_entity(c) for c in d.candidatos],
        )


class ResolverCoordenadasIn(BaseModel):
    """O `candidatoIdx` (elección de un candidato del geocode) o `latitud` +
    `longitud` manuales — el use case valida la combinación."""

    model_config = ConfigDict(populate_by_name=True)
    candidato_idx: int | None = Field(default=None, alias="candidatoIdx")
    latitud: float | None = None
    longitud: float | None = None


class PinSospechosoOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    siges_sucursal_id: int = Field(serialization_alias="sigesSucursalId")
    empresa_nombre: str = Field(serialization_alias="empresaNombre")
    sucursal_nombre: str = Field(serialization_alias="sucursalNombre")
    direccion: str
    latitud_siges: float = Field(serialization_alias="latitudSiges")
    longitud_siges: float = Field(serialization_alias="longitudSiges")
    latitud_geocode: float = Field(serialization_alias="latitudGeocode")
    longitud_geocode: float = Field(serialization_alias="longitudGeocode")
    formatted_address: str = Field(serialization_alias="formattedAddress")
    location_type: str = Field(serialization_alias="locationType")
    discrepancia_km: float = Field(serialization_alias="discrepanciaKm")

    @classmethod
    def from_dto(cls, p: PinSospechoso) -> PinSospechosoOut:
        return cls(
            siges_sucursal_id=p.siges_sucursal_id,
            empresa_nombre=p.empresa_nombre,
            sucursal_nombre=p.sucursal_nombre,
            direccion=p.direccion,
            latitud_siges=p.latitud_siges,
            longitud_siges=p.longitud_siges,
            latitud_geocode=p.latitud_geocode,
            longitud_geocode=p.longitud_geocode,
            formatted_address=p.formatted_address,
            location_type=p.location_type,
            discrepancia_km=p.discrepancia_km,
        )


class AuditarPinesOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    geocodificadas: int
    ya_en_cache: int = Field(serialization_alias="yaEnCache")
    sin_direccion: int = Field(serialization_alias="sinDireccion")
    pendientes_por_tope: int = Field(serialization_alias="pendientesPorTope")
    llamadas_google: int = Field(serialization_alias="llamadasGoogle")

    @classmethod
    def from_dto(cls, r: AuditarPinesResultado) -> AuditarPinesOut:
        return cls(
            geocodificadas=r.geocodificadas,
            ya_en_cache=r.ya_en_cache,
            sin_direccion=r.sin_direccion,
            pendientes_por_tope=r.pendientes_por_tope,
            llamadas_google=r.llamadas_google,
        )
