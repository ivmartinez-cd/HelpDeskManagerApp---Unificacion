import uuid
from dataclasses import dataclass
from datetime import time


@dataclass(slots=True, eq=False)
class Slot:
    """Franja horaria dentro de una casilla, para un día de semana."""

    id: uuid.UUID
    casilla_id: uuid.UUID
    hora_inicio: time
    hora_fin: time
    dia_semana: int  # 0=lunes … 6=domingo
    sort_order: int

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Slot) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
