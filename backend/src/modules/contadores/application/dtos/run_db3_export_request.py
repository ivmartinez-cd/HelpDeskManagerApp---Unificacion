from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class RunDb3ExportRequest:
    file_paths: list[str]
    base_name: str
    output_dir: str
    fecha_maxima: date | None = None
