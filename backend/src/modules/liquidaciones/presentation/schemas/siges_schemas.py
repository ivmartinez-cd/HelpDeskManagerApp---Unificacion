"""Schemas del vínculo y sync de configuración contra Siges (ADR-014)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.dtos.siges_config import (
    PropuestasVinculoResultado,
    SyncSigesResultado,
)
from src.modules.liquidaciones.application.dtos.siges_sucursales import SucursalSigesDTO
from src.modules.liquidaciones.application.dtos.siges_tarifarios import (
    SyncTarifariosResultado,
    ZonasSigesResultado,
)
from src.modules.liquidaciones.domain.entities.tarifario_zona_map import TarifarioZonaMap


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


class VincularBaseSucursalIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    siges_base_sucursal_id: int | None = Field(default=None, alias="sigesBaseSucursalId")


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


# ─── Alta asistida de Tabla KM (ADR-014 dataset 3) ───────────────────────────


class SucursalSigesOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    siges_sucursal_id: int = Field(serialization_alias="sigesSucursalId")
    empresa_nombre: str = Field(serialization_alias="empresaNombre")
    sucursal_nombre: str = Field(serialization_alias="sucursalNombre")
    domicilio: str | None
    localidad: str | None
    provincia: str | None
    ya_cargada: bool = Field(serialization_alias="yaCargada")
    actividad_reciente: bool = Field(serialization_alias="actividadReciente")

    @classmethod
    def from_dto(cls, dto: SucursalSigesDTO) -> SucursalSigesOut:
        return cls(
            siges_sucursal_id=dto.siges_sucursal_id,
            empresa_nombre=dto.empresa_nombre,
            sucursal_nombre=dto.sucursal_nombre,
            domicilio=dto.domicilio,
            localidad=dto.localidad,
            provincia=dto.provincia,
            ya_cargada=dto.ya_cargada,
            actividad_reciente=dto.actividad_reciente,
        )


# ─── Tarifarios (ADR-014 dataset 2) ──────────────────────────────────────────


class ZonaEstadoOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    prestador_id: uuid.UUID = Field(serialization_alias="prestadorId")
    prestador: str
    descripcion_siges: str = Field(serialization_alias="descripcionSiges")
    mapeada: bool
    zona_local: str | None = Field(serialization_alias="zonaLocal")
    propuesta: str | None
    zonas_locales: list[str] = Field(serialization_alias="zonasLocales")


class ZonasSigesOut(BaseModel):
    zonas: list[ZonaEstadoOut]

    @classmethod
    def from_dto(cls, dto: ZonasSigesResultado) -> ZonasSigesOut:
        return cls(
            zonas=[
                ZonaEstadoOut(
                    prestador_id=z.prestador_id,
                    prestador=z.prestador,
                    descripcion_siges=z.descripcion_siges,
                    mapeada=z.mapeada,
                    zona_local=z.zona_local,
                    propuesta=z.propuesta,
                    zonas_locales=z.zonas_locales,
                )
                for z in dto.zonas
            ]
        )


class MapearZonaIn(BaseModel):
    """`zonaLocal` null = mapear a la zona genérica (tarifario sin zona)."""

    model_config = ConfigDict(populate_by_name=True)
    prestador_id: uuid.UUID = Field(alias="prestadorId")
    descripcion_siges: str = Field(alias="descripcionSiges", min_length=1)
    zona_local: str | None = Field(default=None, alias="zonaLocal", min_length=1)


class ZonaMapOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: uuid.UUID
    prestador_id: uuid.UUID = Field(serialization_alias="prestadorId")
    descripcion_siges: str = Field(serialization_alias="descripcionSiges")
    zona_local: str | None = Field(serialization_alias="zonaLocal")

    @classmethod
    def from_entity(cls, e: TarifarioZonaMap) -> ZonaMapOut:
        return cls(
            id=e.id,
            prestador_id=e.prestador_id,
            descripcion_siges=e.descripcion_siges,
            zona_local=e.zona_local,
        )


class GrupoTarifasCreadasOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    prestador: str
    tipo_servicio: str = Field(serialization_alias="tipoServicio")
    zona: str | None
    cantidad: int


class ConflictoTarifarioOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    prestador: str
    tipo_servicio: str = Field(serialization_alias="tipoServicio")
    zona: str | None
    vigencia_desde: str = Field(serialization_alias="vigenciaDesde")
    campo: str
    valor_local: float = Field(serialization_alias="valorLocal")
    valor_siges: float = Field(serialization_alias="valorSiges")


class ZonaSinMapearOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    prestador: str
    descripcion_siges: str = Field(serialization_alias="descripcionSiges")
    filas: int


class SyncTarifariosOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    dry_run: bool = Field(serialization_alias="dryRun")
    creados: int
    grupos_creados: list[GrupoTarifasCreadasOut] = Field(serialization_alias="gruposCreados")
    conflictos: list[ConflictoTarifarioOut]
    sin_cambios: int = Field(serialization_alias="sinCambios")
    zonas_sin_mapear: list[ZonaSinMapearOut] = Field(serialization_alias="zonasSinMapear")
    prestadores_sin_vinculo: list[str] = Field(serialization_alias="prestadoresSinVinculo")

    @classmethod
    def from_dto(cls, dto: SyncTarifariosResultado) -> SyncTarifariosOut:
        return cls(
            dry_run=dto.dry_run,
            creados=dto.creados,
            grupos_creados=[
                GrupoTarifasCreadasOut(
                    prestador=g.prestador,
                    tipo_servicio=g.tipo_servicio,
                    zona=g.zona,
                    cantidad=g.cantidad,
                )
                for g in dto.grupos_creados
            ],
            conflictos=[
                ConflictoTarifarioOut(
                    prestador=c.prestador,
                    tipo_servicio=c.tipo_servicio,
                    zona=c.zona,
                    vigencia_desde=c.vigencia_desde.isoformat(),
                    campo=c.campo,
                    valor_local=c.valor_local,
                    valor_siges=c.valor_siges,
                )
                for c in dto.conflictos
            ],
            sin_cambios=dto.sin_cambios,
            zonas_sin_mapear=[
                ZonaSinMapearOut(
                    prestador=z.prestador,
                    descripcion_siges=z.descripcion_siges,
                    filas=z.filas,
                )
                for z in dto.zonas_sin_mapear
            ],
            prestadores_sin_vinculo=dto.prestadores_sin_vinculo,
        )
