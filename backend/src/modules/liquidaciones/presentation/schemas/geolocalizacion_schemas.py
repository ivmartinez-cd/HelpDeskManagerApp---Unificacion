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
from src.modules.liquidaciones.application.use_cases.tabla_km_refrescar_siges import (
    CambioDomicilio,
    FilaNoEncontrada,
    RefrescarDireccionesResultado,
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
    sin_actividad: int = Field(serialization_alias="sinActividad")

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
            sin_actividad=r.sin_actividad,
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


class CambioDomicilioOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    sucursal_nombre: str = Field(serialization_alias="sucursalNombre")
    empresa_nombre: str = Field(serialization_alias="empresaNombre")
    domicilio_antes: str | None = Field(serialization_alias="domicilioAntes")
    domicilio_despues: str | None = Field(serialization_alias="domicilioDespues")

    @classmethod
    def from_dto(cls, c: CambioDomicilio) -> CambioDomicilioOut:
        return cls(
            sucursal_nombre=c.sucursal_nombre,
            empresa_nombre=c.empresa_nombre,
            domicilio_antes=c.domicilio_antes,
            domicilio_despues=c.domicilio_despues,
        )


class FilaNoEncontradaOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    empresa_nombre: str = Field(serialization_alias="empresaNombre")
    sucursal_nombre: str = Field(serialization_alias="sucursalNombre")

    @classmethod
    def from_dto(cls, f: FilaNoEncontrada) -> FilaNoEncontradaOut:
        return cls(empresa_nombre=f.empresa_nombre, sucursal_nombre=f.sucursal_nombre)


class RefrescarDireccionesOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    actualizadas: int
    sin_cambios: int = Field(serialization_alias="sinCambios")
    no_encontradas: int = Field(serialization_alias="noEncontradas")
    vinculadas: int = 0
    cambios: list[CambioDomicilioOut]
    no_encontradas_detalle: list[FilaNoEncontradaOut] = Field(
        serialization_alias="noEncontradasDetalle", default_factory=list
    )

    @classmethod
    def from_dto(cls, r: RefrescarDireccionesResultado) -> RefrescarDireccionesOut:
        return cls(
            actualizadas=r.actualizadas,
            sin_cambios=r.sin_cambios,
            no_encontradas=r.no_encontradas,
            vinculadas=r.vinculadas,
            cambios=[CambioDomicilioOut.from_dto(c) for c in r.cambios],
            no_encontradas_detalle=[
                FilaNoEncontradaOut.from_dto(f) for f in r.no_encontradas_detalle
            ],
        )
