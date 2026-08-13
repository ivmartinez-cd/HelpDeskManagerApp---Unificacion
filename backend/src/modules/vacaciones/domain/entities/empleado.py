import uuid
from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class EstadoEmpleado(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass(slots=True, eq=False)
class Empleado:
    """Entidad: identidad por `id`. `user_id` es el vínculo opcional con la
    cuenta `app_user` de la plataforma (D3 del plan)."""

    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    hire_date: date
    annual_vacation_days: int
    status: EstadoEmpleado
    color: str
    department_id: uuid.UUID
    cargo_id: uuid.UUID
    user_id: uuid.UUID | None

    @property
    def nombre_completo(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def esta_activo(self) -> bool:
        return self.status is EstadoEmpleado.ACTIVE

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Empleado) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
