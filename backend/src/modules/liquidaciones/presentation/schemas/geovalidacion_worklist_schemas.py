"""Schemas del worklist final de geovalidación (Fase 2, cierre)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.use_cases.geovalidacion_worklist import (
    ItemWorklist,
    ResultadoWorklistTier2,
)


class ItemWorklistOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    siges_sucursal_id: int = Field(serialization_alias="sigesSucursalId")
    empresa_nombre: str = Field(serialization_alias="empresaNombre")
    sucursal_nombre: str = Field(serialization_alias="sucursalNombre")
    domicilio: str | None
    motivos: list[str]

    @classmethod
    def from_dto(cls, i: ItemWorklist) -> ItemWorklistOut:
        return cls(
            siges_sucursal_id=i.siges_sucursal_id,
            empresa_nombre=i.empresa_nombre,
            sucursal_nombre=i.sucursal_nombre,
            domicilio=i.domicilio,
            motivos=i.motivos,
        )


class ResultadoWorklistTier2Out(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    certeza_absoluta: list[ItemWorklistOut] = Field(serialization_alias="certezaAbsoluta")
    requiere_verificacion: list[ItemWorklistOut] = Field(serialization_alias="requiereVerificacion")
    estimacion_llamadas_google: int = Field(serialization_alias="estimacionLlamadasGoogle")

    @classmethod
    def from_dto(cls, r: ResultadoWorklistTier2) -> ResultadoWorklistTier2Out:
        return cls(
            certeza_absoluta=[ItemWorklistOut.from_dto(i) for i in r.certeza_absoluta],
            requiere_verificacion=[ItemWorklistOut.from_dto(i) for i in r.requiere_verificacion],
            estimacion_llamadas_google=r.estimacion_llamadas_google,
        )
