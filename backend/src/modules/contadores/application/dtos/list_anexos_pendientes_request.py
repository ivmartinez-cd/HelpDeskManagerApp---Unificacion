from dataclasses import dataclass
from typing import Literal

FiltroEstado = Literal["todos", "en_proceso", "demorado", "mes_en_curso"]


@dataclass(frozen=True)
class ListAnexosPendientesRequest:
    estado: FiltroEstado = "todos"
    search: str | None = None
    force_refresh: bool = False
