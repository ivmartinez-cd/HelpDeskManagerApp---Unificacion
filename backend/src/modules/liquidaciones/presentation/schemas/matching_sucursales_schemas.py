"""Schemas del matching de sucursales de Tabla KM ↔ Siges (Fase 1)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.use_cases.matching_sucursales_tabla_km import (
    CandidatoN2Detalle,
    PropuestaN2,
    ResultadoAutoVinculoN1,
    VinculoN1Aplicado,
)


class VinculoN1AplicadoOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    tabla_km_id: str = Field(serialization_alias="tablaKmId")
    empresa_nombre: str = Field(serialization_alias="empresaNombre")
    sucursal_nombre: str = Field(serialization_alias="sucursalNombre")
    siges_sucursal_id: int = Field(serialization_alias="sigesSucursalId")

    @classmethod
    def from_dto(cls, v: VinculoN1Aplicado) -> VinculoN1AplicadoOut:
        return cls(
            tabla_km_id=str(v.tabla_km_id),
            empresa_nombre=v.empresa_nombre,
            sucursal_nombre=v.sucursal_nombre,
            siges_sucursal_id=v.siges_sucursal_id,
        )


class ResultadoAutoVinculoN1Out(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    vinculadas: int
    sin_cambios: int = Field(serialization_alias="sinCambios")
    detalle: list[VinculoN1AplicadoOut]

    @classmethod
    def from_dto(cls, r: ResultadoAutoVinculoN1) -> ResultadoAutoVinculoN1Out:
        return cls(
            vinculadas=r.vinculadas,
            sin_cambios=r.sin_cambios,
            detalle=[VinculoN1AplicadoOut.from_dto(v) for v in r.detalle],
        )


class CandidatoN2Out(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    siges_sucursal_id: int = Field(serialization_alias="sigesSucursalId")
    sucursal_nombre: str = Field(serialization_alias="sucursalNombre")
    domicilio: str | None
    score: float
    motivo: str
    misma_direccion: bool = Field(serialization_alias="mismaDireccion")

    @classmethod
    def from_dto(cls, c: CandidatoN2Detalle) -> CandidatoN2Out:
        return cls(
            siges_sucursal_id=c.siges_sucursal_id,
            sucursal_nombre=c.sucursal_nombre,
            domicilio=c.domicilio,
            score=round(c.score, 3),
            motivo=c.motivo,
            misma_direccion=c.misma_direccion,
        )


class PropuestaN2Out(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    tabla_km_id: str = Field(serialization_alias="tablaKmId")
    empresa_nombre: str = Field(serialization_alias="empresaNombre")
    sucursal_nombre: str = Field(serialization_alias="sucursalNombre")
    candidatos: list[CandidatoN2Out]

    @classmethod
    def from_dto(cls, p: PropuestaN2) -> PropuestaN2Out:
        return cls(
            tabla_km_id=str(p.tabla_km_id),
            empresa_nombre=p.empresa_nombre,
            sucursal_nombre=p.sucursal_nombre,
            candidatos=[CandidatoN2Out.from_dto(c) for c in p.candidatos],
        )


class ConfirmarVinculoIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    siges_sucursal_id: int = Field(alias="sigesSucursalId")


class RechazarPropuestaIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    siges_sucursal_id: int = Field(alias="sigesSucursalId")
