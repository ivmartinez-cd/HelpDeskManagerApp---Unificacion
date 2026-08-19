"""Schema del worklist de Tier 0 (Fase 2 del plan de matching + geovalidación)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.use_cases.geovalidacion_tier0 import (
    HallazgoTier0Detalle,
)


class HallazgoTier0Out(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    siges_sucursal_id: int = Field(serialization_alias="sigesSucursalId")
    empresa_nombre: str = Field(serialization_alias="empresaNombre")
    sucursal_nombre: str = Field(serialization_alias="sucursalNombre")
    domicilio: str | None
    latitud: float | None
    longitud: float | None
    severidad: str
    codigo: str
    detalle: str

    @classmethod
    def from_dto(cls, h: HallazgoTier0Detalle) -> HallazgoTier0Out:
        return cls(
            siges_sucursal_id=h.siges_sucursal_id,
            empresa_nombre=h.empresa_nombre,
            sucursal_nombre=h.sucursal_nombre,
            domicilio=h.domicilio,
            latitud=h.latitud,
            longitud=h.longitud,
            severidad=h.severidad,
            codigo=h.codigo,
            detalle=h.detalle,
        )
