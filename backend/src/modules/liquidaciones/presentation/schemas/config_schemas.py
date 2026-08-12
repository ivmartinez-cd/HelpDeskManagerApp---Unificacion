"""Schemas de configuración — prestadores, SPSTs, tarifarios, tabla KM."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario

# ─── Prestadores ─────────────────────────────────────────────────────────────


class PrestadorIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    nombre: str
    nombre_corto: str = Field(alias="nombreCorto")
    cuit: str | None = None
    region: str | None = None


class PrestadorOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: uuid.UUID
    nombre: str
    nombre_corto: str = Field(serialization_alias="nombreCorto")
    cuit: str | None
    region: str | None
    activo: bool
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    @classmethod
    def from_entity(cls, e: Prestador) -> PrestadorOut:
        return cls(
            id=e.id,
            nombre=e.nombre,
            nombre_corto=e.nombre_corto,
            cuit=e.cuit,
            region=e.region,
            activo=e.activo,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )


class ToggleActivoIn(BaseModel):
    activo: bool


# ─── SPSTs ───────────────────────────────────────────────────────────────────


class SpstIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    prestador_id: uuid.UUID = Field(alias="prestadorId")
    nombre: str
    domicilio: str | None = None
    localidad: str | None = None
    provincia: str | None = None
    zona: str | None = None


class SpstOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: uuid.UUID
    prestador_id: uuid.UUID = Field(serialization_alias="prestadorId")
    nombre: str
    domicilio: str | None
    localidad: str | None
    provincia: str | None
    zona: str | None
    activo: bool
    created_at: datetime = Field(serialization_alias="createdAt")

    @classmethod
    def from_entity(cls, e: Spst) -> SpstOut:
        return cls(
            id=e.id,
            prestador_id=e.prestador_id,
            nombre=e.nombre,
            domicilio=e.domicilio,
            localidad=e.localidad,
            provincia=e.provincia,
            zona=e.zona,
            activo=e.activo,
            created_at=e.created_at,
        )


# ─── Tarifarios ──────────────────────────────────────────────────────────────


class TarifarioIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    prestador_id: uuid.UUID = Field(alias="prestadorId")
    tipo_servicio: str = Field(alias="tipoServicio")
    zona: str | None = None
    costo_servicio: float = Field(alias="costoServicio")
    costo_km: float = Field(alias="costoKm")
    vigencia_desde: date = Field(alias="vigenciaDesde")
    vigencia_hasta: date | None = Field(default=None, alias="vigenciaHasta")


class TarifarioOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: uuid.UUID
    prestador_id: uuid.UUID = Field(serialization_alias="prestadorId")
    tipo_servicio: str = Field(serialization_alias="tipoServicio")
    zona: str | None
    costo_servicio: float = Field(serialization_alias="costoServicio")
    costo_km: float = Field(serialization_alias="costoKm")
    vigencia_desde: date = Field(serialization_alias="vigenciaDesde")
    vigencia_hasta: date | None = Field(serialization_alias="vigenciaHasta")
    created_at: datetime = Field(serialization_alias="createdAt")

    @classmethod
    def from_entity(cls, e: Tarifario) -> TarifarioOut:
        return cls(
            id=e.id,
            prestador_id=e.prestador_id,
            tipo_servicio=e.tipo_servicio,
            zona=e.zona,
            costo_servicio=e.costo_servicio,
            costo_km=e.costo_km,
            vigencia_desde=e.vigencia_desde,
            vigencia_hasta=e.vigencia_hasta,
            created_at=e.created_at,
        )


# ─── Tabla KM ────────────────────────────────────────────────────────────────


class TablaKmIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    prestador_id: uuid.UUID = Field(alias="prestadorId")
    spst_id: uuid.UUID | None = Field(default=None, alias="spstId")
    empresa_nombre: str = Field(alias="empresaNombre")
    sucursal_nombre: str = Field(alias="sucursalNombre")
    observaciones: str | None = None
    domicilio_cliente: str | None = Field(default=None, alias="domicilioCliente")
    localidad_cliente: str | None = Field(default=None, alias="localidadCliente")
    provincia_cliente: str | None = Field(default=None, alias="provinciaCliente")
    kms_recorrido: float = Field(alias="kmsRecorrido")
    umbral_viatico: float = Field(default=30.0, alias="umbralViatico")
    aplica_viatico: bool = Field(default=False, alias="aplicaViatico")
    kms_a_facturar: float = Field(default=0.0, alias="kmsAFacturar")
    url_maps: str | None = Field(default=None, alias="urlMaps")


class TablaKmOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: uuid.UUID
    prestador_id: uuid.UUID = Field(serialization_alias="prestadorId")
    spst_id: uuid.UUID | None = Field(serialization_alias="spstId")
    empresa_nombre: str = Field(serialization_alias="empresaNombre")
    sucursal_nombre: str = Field(serialization_alias="sucursalNombre")
    observaciones: str | None
    domicilio_cliente: str | None = Field(serialization_alias="domicilioCliente")
    localidad_cliente: str | None = Field(serialization_alias="localidadCliente")
    provincia_cliente: str | None = Field(serialization_alias="provinciaCliente")
    kms_recorrido: float = Field(serialization_alias="kmsRecorrido")
    umbral_viatico: float = Field(serialization_alias="umbralViatico")
    aplica_viatico: bool = Field(serialization_alias="aplicaViatico")
    kms_a_facturar: float = Field(serialization_alias="kmsAFacturar")
    url_maps: str | None = Field(serialization_alias="urlMaps")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    @classmethod
    def from_entity(cls, e: TablaKm) -> TablaKmOut:
        return cls(
            id=e.id,
            prestador_id=e.prestador_id,
            spst_id=e.spst_id,
            empresa_nombre=e.empresa_nombre,
            sucursal_nombre=e.sucursal_nombre,
            observaciones=e.observaciones,
            domicilio_cliente=e.domicilio_cliente,
            localidad_cliente=e.localidad_cliente,
            provincia_cliente=e.provincia_cliente,
            kms_recorrido=e.kms_recorrido,
            umbral_viatico=e.umbral_viatico,
            aplica_viatico=e.aplica_viatico,
            kms_a_facturar=e.kms_a_facturar,
            url_maps=e.url_maps,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
