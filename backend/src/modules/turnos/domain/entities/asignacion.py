import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(slots=True, eq=False)
class Asignacion:
    """Asignación de un usuario a un slot de turno."""

    id: uuid.UUID
    slot_id: uuid.UUID
    user_id: uuid.UUID
    vigente_desde: date
    vigente_hasta: date | None  # None = indefinida

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Asignacion) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
