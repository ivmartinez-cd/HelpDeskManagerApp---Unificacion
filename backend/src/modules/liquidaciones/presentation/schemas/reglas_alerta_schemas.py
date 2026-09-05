"""Schemas del catálogo de reglas de alerta (ALT001-009)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.domain.entities.regla_alerta import (
    CODIGOS_CON_EVALUADOR,
    ReglaAlerta,
    genera_observaciones,
)


class ReglaAlertaOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    codigo: str
    nombre: str
    descripcion: str | None
    activa: bool
    riesgo_base: float = Field(serialization_alias="riesgoBase")
    # ALT006/ALT007 existen en el catálogo pero no tienen evaluador: activarlas
    # no genera nada — la UI lo señala para que no confunda.
    tiene_evaluador: bool = Field(serialization_alias="tieneEvaluador")
    # Segundo switch, hoy solo relevante para ALT005 (ver `genera_observaciones`
    # en el dominio) — requiere `activa=True` además de este flag.
    genera_observaciones: bool = Field(serialization_alias="generaObservaciones")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    @classmethod
    def from_entity(cls, r: ReglaAlerta) -> ReglaAlertaOut:
        return cls(
            id=r.id,
            codigo=r.codigo,
            nombre=r.nombre,
            descripcion=r.descripcion,
            activa=r.activa,
            riesgo_base=r.riesgo_base,
            tiene_evaluador=r.codigo in CODIGOS_CON_EVALUADOR,
            genera_observaciones=genera_observaciones(r),
            updated_at=r.updated_at,
        )


class ReglaActivaIn(BaseModel):
    activa: bool


class ReglaGeneraObservacionesIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    genera_observaciones: bool = Field(alias="generaObservaciones")
