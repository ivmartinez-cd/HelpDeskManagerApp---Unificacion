import uuid
from dataclasses import dataclass


@dataclass(slots=True, eq=False)
class Casilla:
    """Una casilla de correo (ej. INSUMOS, ST) a la que se asignan turnos."""

    id: uuid.UUID
    nombre: str
    color: str | None
    sort_order: int
    is_active: bool

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Casilla) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
