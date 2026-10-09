import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, eq=False)
class Ciclo:
    """Ciclo anual de vacaciones de un empleado. `annual_days` se fija al
    crearlo según la antigüedad proyectada al 1/1 del año; `carry_over` se
    recalcula con write-behind en cada lectura de saldo (paridad legacy).

    `ajuste_inicial` es la diferencia entre el saldo anotado en la planilla de
    RRHH importada al legacy y los días que da la antigüedad: negativo = días
    tomados antes de usar el sistema, positivo = arrastre previo. Solo lo
    escribe la migración de datos; la app lo lee y nunca lo recalcula.
    """

    id: uuid.UUID
    empleado_id: uuid.UUID
    year: int
    annual_days: int
    carry_over: int
    is_open: bool
    opened_at: datetime | None
    ajuste_inicial: int = 0

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Ciclo) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
