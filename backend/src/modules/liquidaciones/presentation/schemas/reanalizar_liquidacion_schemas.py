"""Schema de POST /api/liquidaciones/{id}/reanalyze."""

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.dtos.reanalizar_liquidacion import (
    ReanalizarLiquidacionResultado,
)


class ReanalizarLiquidacionOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_incidentes: int = Field(serialization_alias="totalIncidentes")
    total_alertas: int = Field(serialization_alias="totalAlertas")
    total_observaciones: int = Field(serialization_alias="totalObservaciones")

    @classmethod
    def from_dto(cls, dto: ReanalizarLiquidacionResultado) -> "ReanalizarLiquidacionOut":
        return cls(
            total_incidentes=dto.total_incidentes,
            total_alertas=dto.total_alertas,
            total_observaciones=dto.total_observaciones,
        )
