"""Schemas del vínculo y sync de configuración contra Siges (ADR-014)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.dtos.siges_config import (
    PropuestasVinculoResultado,
    SyncSigesResultado,
)


class SigesEmpresaOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    siges_empresa_id: int = Field(serialization_alias="sigesEmpresaId")
    den_comercial: str = Field(serialization_alias="denComercial")
    razon_social: str | None = Field(serialization_alias="razonSocial")
    cuit: str | None
    tipo: str


class PropuestaVinculoOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    entidad: str
    local_id: uuid.UUID = Field(serialization_alias="localId")
    local_nombre: str = Field(serialization_alias="localNombre")
    siges_empresa_id: int = Field(serialization_alias="sigesEmpresaId")
    siges_den_comercial: str = Field(serialization_alias="sigesDenComercial")


class PropuestasVinculoOut(BaseModel):
    propuestas: list[PropuestaVinculoOut]
    disponibles: list[SigesEmpresaOut]

    @classmethod
    def from_dto(cls, dto: PropuestasVinculoResultado) -> PropuestasVinculoOut:
        return cls(
            propuestas=[
                PropuestaVinculoOut(
                    entidad=p.entidad,
                    local_id=p.local_id,
                    local_nombre=p.local_nombre,
                    siges_empresa_id=p.siges_empresa_id,
                    siges_den_comercial=p.siges_den_comercial,
                )
                for p in dto.propuestas
            ],
            disponibles=[
                SigesEmpresaOut(
                    siges_empresa_id=e.siges_empresa_id,
                    den_comercial=e.den_comercial,
                    razon_social=e.razon_social,
                    cuit=e.cuit,
                    tipo=e.tipo,
                )
                for e in dto.disponibles
            ],
        )


class VincularSigesIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    siges_empresa_id: int | None = Field(default=None, alias="sigesEmpresaId")


class SyncCambioOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    local_id: uuid.UUID = Field(serialization_alias="localId")
    local_nombre: str = Field(serialization_alias="localNombre")
    campo: str
    valor_anterior: str | None = Field(serialization_alias="valorAnterior")
    valor_nuevo: str | None = Field(serialization_alias="valorNuevo")


class SyncDiferenciaNombreOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    local_id: uuid.UUID = Field(serialization_alias="localId")
    local_nombre: str = Field(serialization_alias="localNombre")
    siges_den_comercial: str = Field(serialization_alias="sigesDenComercial")


class SyncSigesOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    dry_run: bool = Field(serialization_alias="dryRun")
    cambios: list[SyncCambioOut]
    nombres_distintos: list[SyncDiferenciaNombreOut] = Field(
        serialization_alias="nombresDistintos"
    )
    sin_cambios: int = Field(serialization_alias="sinCambios")
    sin_vinculo: list[str] = Field(serialization_alias="sinVinculo")
    vinculo_roto: list[str] = Field(serialization_alias="vinculoRoto")

    @classmethod
    def from_dto(cls, dto: SyncSigesResultado) -> SyncSigesOut:
        return cls(
            dry_run=dto.dry_run,
            cambios=[
                SyncCambioOut(
                    local_id=c.local_id,
                    local_nombre=c.local_nombre,
                    campo=c.campo,
                    valor_anterior=c.valor_anterior,
                    valor_nuevo=c.valor_nuevo,
                )
                for c in dto.cambios
            ],
            nombres_distintos=[
                SyncDiferenciaNombreOut(
                    local_id=d.local_id,
                    local_nombre=d.local_nombre,
                    siges_den_comercial=d.siges_den_comercial,
                )
                for d in dto.nombres_distintos
            ],
            sin_cambios=dto.sin_cambios,
            sin_vinculo=dto.sin_vinculo,
            vinculo_roto=dto.vinculo_roto,
        )
