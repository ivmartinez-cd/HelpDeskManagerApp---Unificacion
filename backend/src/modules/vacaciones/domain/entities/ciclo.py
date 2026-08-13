import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, eq=False)
class Ciclo:
    """Ciclo anual de vacaciones de un empleado. `annual_days` se fija al
    crearlo según la antigüedad proyectada al 1/1 del año; `carry_over` se
    recalcula con write-behind en cada lectura de saldo (paridad legacy)."""

    id: uuid.UUID
    empleado_id: uuid.UUID
    year: int
    annual_days: int
    carry_over: int
    is_open: bool
    opened_at: datetime | None

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Ciclo) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
