"""Schema de respuesta del backfill de estado de liquidaciones."""

from pydantic import BaseModel, ConfigDict, Field

from src.modules.liquidaciones.application.dtos.backfill_estado import BackfillEstadoResultado


class BackfillEstadoPrestadorOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    prestador_id: str = Field(serialization_alias="prestadorId")
    prestador_nombre: str = Field(serialization_alias="prestadorNombre")
    procesadas: int
    actualizadas: int
    saltadas: int
    sin_match: int = Field(serialization_alias="sinMatch")


class BackfillEstadoOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dry_run: bool = Field(serialization_alias="dryRun")
    total_actualizadas: int = Field(serialization_alias="totalActualizadas")
    total_saltadas: int = Field(serialization_alias="totalSaltadas")
    por_estado_destino: dict[str, int] = Field(serialization_alias="porEstadoDestino")
    prestadores: list[BackfillEstadoPrestadorOut]

    @classmethod
    def from_dto(cls, dto: BackfillEstadoResultado) -> "BackfillEstadoOut":
        return cls(
            dry_run=dto.dry_run,
            total_actualizadas=dto.total_actualizadas,
            total_saltadas=dto.total_saltadas,
            por_estado_destino=dto.por_estado_destino,
            prestadores=[
                BackfillEstadoPrestadorOut(
                    prestador_id=p.prestador_id,
                    prestador_nombre=p.prestador_nombre,
                    procesadas=p.procesadas,
                    actualizadas=p.actualizadas,
                    saltadas=p.saltadas,
                    sin_match=p.sin_match,
                )
                for p in dto.prestadores
            ],
        )
