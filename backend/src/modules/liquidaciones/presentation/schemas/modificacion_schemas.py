"""Schemas de `GET /liquidaciones/{id}/modificaciones` y afines — ver ADR-038."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.domain.entities.modificacion_prestador import (
    ModificacionPrestador,
)


class ModificacionOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    liquidacion_id: uuid.UUID = Field(serialization_alias="liquidacionId")
    # Desnormalizado en la respuesta (no en la entidad) para que el frontend
    # arme el toast ("Liquidación 3925-1: ...") sin una segunda consulta.
    numero_liquidacion: str | None = Field(serialization_alias="numeroLiquidacion")
    numero_incidente: str = Field(serialization_alias="numeroIncidente")
    tipo_cambio: str = Field(serialization_alias="tipoCambio")
    campo: str | None
    valor_anterior: str | None = Field(serialization_alias="valorAnterior")
    valor_nuevo: str | None = Field(serialization_alias="valorNuevo")
    detectada_en: datetime = Field(serialization_alias="detectadaEn")
    vista_en: datetime | None = Field(serialization_alias="vistaEn")

    @classmethod
    def from_entity(
        cls, e: ModificacionPrestador, *, numero_liquidacion: str | None
    ) -> "ModificacionOut":
        return cls(
            id=e.id,
            liquidacion_id=e.liquidacion_id,
            numero_liquidacion=numero_liquidacion,
            numero_incidente=e.numero_incidente,
            tipo_cambio=e.tipo_cambio,
            campo=e.campo,
            valor_anterior=e.valor_anterior,
            valor_nuevo=e.valor_nuevo,
            detectada_en=e.detectada_en,
            vista_en=e.vista_en,
        )


class MarcarVistasOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    actualizadas: int
