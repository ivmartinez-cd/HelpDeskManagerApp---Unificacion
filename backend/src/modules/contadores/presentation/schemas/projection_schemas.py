from pydantic import BaseModel, ConfigDict, Field

from src.modules.contadores.application.dtos.run_projection_result import RunProjectionResult


class ProjectionSummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total: int
    reales: int
    proyectados: int
    sin_datos: int = Field(serialization_alias="sinDatos")
    dias_mediana: float = Field(serialization_alias="diasMediana")
    dias_max: int = Field(serialization_alias="diasMax")
    consumo_mediana: float = Field(serialization_alias="consumoMediana")
    consumo_max: float = Field(serialization_alias="consumoMax")


class RunProjectionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    summary: ProjectionSummaryResponse
    excel_file: str = Field(serialization_alias="excelFile")
    siges_csv_file: str = Field(serialization_alias="sigesCsvFile")

    @classmethod
    def from_domain(cls, result: RunProjectionResult) -> "RunProjectionResponse":
        return cls(
            summary=ProjectionSummaryResponse(
                total=result.summary.total,
                reales=result.summary.reales,
                proyectados=result.summary.proyectados,
                sin_datos=result.summary.sin_datos,
                dias_mediana=result.summary.dias_mediana,
                dias_max=result.summary.dias_max,
                consumo_mediana=result.summary.consumo_mediana,
                consumo_max=result.summary.consumo_max,
            ),
            excel_file=result.excel_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1],
            siges_csv_file=result.siges_csv_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1],
        )
