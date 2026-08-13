import uuid
from dataclasses import dataclass


@dataclass(slots=True, eq=False)
class Sector:
    """Sector/departamento. Mapea a la tabla `department` compartida con auth
    (D1 del plan): auth la usa para alcance sectorial, vacaciones para el ABM
    de Gestión Humana y el color de los eventos del calendario."""

    id: uuid.UUID
    name: str
    color: str
    is_active: bool

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Sector) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
