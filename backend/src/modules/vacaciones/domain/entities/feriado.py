import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(slots=True, eq=False)
class Feriado:
    """Feriado. Con `deducts_vacation=False` (default legacy) el feriado que
    cae exactamente en el inicio de una solicitud desplaza el conteo (-1 día);
    con True cuenta como día corrido normal. Los feriados en el medio del
    rango cuentan siempre (LCT)."""

    id: uuid.UUID
    name: str
    date: date
    deducts_vacation: bool

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Feriado) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
