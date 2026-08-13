import uuid
from dataclasses import dataclass


@dataclass(slots=True, eq=False)
class Exclusion:
    """Par de empleados que no pueden solapar vacaciones. El par se guarda
    normalizado (`empleado_a_id < empleado_b_id`, CHECK en schema)."""

    id: uuid.UUID
    empleado_a_id: uuid.UUID
    empleado_b_id: uuid.UUID

    def contraparte_de(self, empleado_id: uuid.UUID) -> uuid.UUID | None:
        if empleado_id == self.empleado_a_id:
            return self.empleado_b_id
        if empleado_id == self.empleado_b_id:
            return self.empleado_a_id
        return None

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Exclusion) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
