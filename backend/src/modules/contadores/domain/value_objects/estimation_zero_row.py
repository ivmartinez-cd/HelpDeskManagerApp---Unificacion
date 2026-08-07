from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EstimationZeroRow:
    serie: str
    fecha: str
    tipo: str
    clase_10: str
    contador_10: int
    clase_20: str
    contador_20: int
