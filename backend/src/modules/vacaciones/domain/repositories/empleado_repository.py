import uuid
from dataclasses import dataclass
from typing import Protocol

from src.modules.vacaciones.domain.entities.empleado import Empleado, EstadoEmpleado


@dataclass(frozen=True, slots=True)
class FiltrosEmpleados:
    search: str | None = None
    department_id: uuid.UUID | None = None
    status: EstadoEmpleado | None = None
    empleado_id: uuid.UUID | None = None


class EmpleadoRepository(Protocol):
    async def get_by_id(self, empleado_id: uuid.UUID) -> Empleado | None: ...

    async def get_by_user_id(self, user_id: uuid.UUID) -> Empleado | None: ...

    async def get_by_email(self, email: str) -> Empleado | None: ...

    async def get_by_ids(self, empleado_ids: list[uuid.UUID]) -> dict[uuid.UUID, Empleado]: ...

    async def list_filtrados(self, filtros: FiltrosEmpleados) -> list[Empleado]: ...

    async def count_activos_por_departamento(self, department_id: uuid.UUID) -> int: ...

    async def add(self, empleado: Empleado) -> None: ...

    async def save(self, empleado: Empleado) -> None: ...

    async def delete(self, empleado_id: uuid.UUID) -> None: ...

    async def vincular_siges(
        self, empleado_id: uuid.UUID, *, siges_empresa_id: int | None
    ) -> Empleado | None: ...
