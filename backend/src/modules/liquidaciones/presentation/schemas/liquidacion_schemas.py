"""Schemas de GET /api/liquidaciones y GET /api/liquidaciones/{id}. Módulo nuevo, sin
contrato legacy que preservar — snake_case en Python, camelCase en el wire (mismo
patrón que turnos/sla, ver `turno_schemas.py`)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion


class LiquidacionOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    prestador_id: uuid.UUID = Field(serialization_alias="prestadorId")
    numero_liquidacion: str | None = Field(serialization_alias="numeroLiquidacion")
    periodo: str
    tipo_liquidacion: str = Field(serialization_alias="tipoLiquidacion")
    nombre_archivo: str | None = Field(serialization_alias="nombreArchivo")
    fecha_importacion: datetime = Field(serialization_alias="fechaImportacion")
    estado: str
    total_incidentes: int = Field(serialization_alias="totalIncidentes")
    total_alertas: int = Field(serialization_alias="totalAlertas")
    total_importe: float = Field(serialization_alias="totalImporte")

    @classmethod
    def from_entity(cls, e: Liquidacion) -> "LiquidacionOut":
        return cls(
            id=e.id,
            prestador_id=e.prestador_id,
            numero_liquidacion=e.numero_liquidacion,
            periodo=e.periodo,
            tipo_liquidacion=e.tipo_liquidacion,
            nombre_archivo=e.nombre_archivo,
            fecha_importacion=e.fecha_importacion,
            estado=e.estado,
            total_incidentes=e.total_incidentes,
            total_alertas=e.total_alertas,
            total_importe=e.total_importe,
        )
