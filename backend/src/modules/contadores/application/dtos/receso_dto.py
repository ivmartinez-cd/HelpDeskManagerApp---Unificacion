from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class RecesoDto:
    id: int
    id_grupo_economico: int
    id_anexo: int | None
    fecha_desde: date
    fecha_hasta: date
    descripcion: str
