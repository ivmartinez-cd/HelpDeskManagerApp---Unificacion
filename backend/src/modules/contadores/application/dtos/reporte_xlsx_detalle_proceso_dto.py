from dataclasses import dataclass
from typing import Literal

AlcanceReporte = Literal["todos", "falta_contador"]


@dataclass(frozen=True, slots=True)
class ReporteXlsxDetalleProceso:
    filename: str
    contenido: bytes
