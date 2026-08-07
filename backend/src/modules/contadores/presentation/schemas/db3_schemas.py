from pydantic import BaseModel, ConfigDict, Field

from src.modules.contadores.application.dtos.run_db3_export_result import RunDb3ExportResult


class RunDb3ExportResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    csv_file: str = Field(serialization_alias="csvFile")
    row_count: int = Field(serialization_alias="rowCount")
    warnings: list[str]

    @classmethod
    def from_domain(cls, result: RunDb3ExportResult) -> "RunDb3ExportResponse":
        filename = result.csv_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        return cls(csv_file=filename, row_count=result.row_count, warnings=result.warnings)
