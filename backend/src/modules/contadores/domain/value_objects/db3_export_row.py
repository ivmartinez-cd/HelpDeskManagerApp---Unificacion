from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class Db3ExportRow:
    serie: str
    fecha: date
    tipo: int
    clase_10: str
    contador_10: int
    clase_20: str
    contador_20: int
