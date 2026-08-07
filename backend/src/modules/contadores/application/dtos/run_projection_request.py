from dataclasses import dataclass
from datetime import date

from src.modules.contadores.domain.value_objects.projection_settings import ProjectionSettings


@dataclass(frozen=True, slots=True)
class RunProjectionRequest:
    file_path: str
    source_filename: str
    fecha_toma: date
    output_dir: str
    settings: ProjectionSettings = ProjectionSettings()
