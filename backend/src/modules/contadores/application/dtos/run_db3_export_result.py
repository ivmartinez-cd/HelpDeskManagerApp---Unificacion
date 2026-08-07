from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunDb3ExportResult:
    csv_path: str
    warnings: list[str]
    row_count: int
