import uuid
from dataclasses import dataclass


@dataclass(slots=True, eq=False)
class Cargo:
    """Cargo/posición. `max_simultaneos` (None = sin límite) absorbe el
    PositionOverlapLimit legacy: máximo de empleados del cargo con vacaciones
    superpuestas en un mismo día."""

    id: uuid.UUID
    name: str
    max_simultaneos: int | None

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Cargo) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
