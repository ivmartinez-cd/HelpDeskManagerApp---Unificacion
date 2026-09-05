"""Schema de POST /api/liquidaciones/importar."""

import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.dtos.importar_liquidacion import (
    ImportarLiquidacionResultado,
)


class ImportarLiquidacionOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    liquidacion_id: uuid.UUID = Field(serialization_alias="liquidacionId")
    total_incidentes: int = Field(serialization_alias="totalIncidentes")
    total_alertas: int = Field(serialization_alias="totalAlertas")

    @classmethod
    def from_dto(cls, dto: ImportarLiquidacionResultado) -> "ImportarLiquidacionOut":
        return cls(
            liquidacion_id=dto.liquidacion_id,
            total_incidentes=dto.total_incidentes,
            total_alertas=dto.total_alertas,
        )
