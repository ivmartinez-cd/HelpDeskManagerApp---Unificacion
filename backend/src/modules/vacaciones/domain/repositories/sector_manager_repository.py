import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class JefeSector:
    user_id: uuid.UUID
    department_id: uuid.UUID


class SectorManagerRepository(Protocol):
    """Jefe↔sector sobre `user_module_scope` de auth con
    `module_key='vacaciones'` (D2 del plan): una fila con
    `scope_department_id=X` significa "este usuario es jefe del sector X".
    Un usuario gestiona a lo sumo un sector (PK user_id+module_key);
    varios usuarios pueden gestionar el mismo sector.
    """

    async def get_sector_de_usuario(self, user_id: uuid.UUID) -> uuid.UUID | None: ...

    async def list_jefes(self) -> list[JefeSector]: ...

    async def asignar(self, user_id: uuid.UUID, department_id: uuid.UUID) -> None: ...

    async def desasignar(self, user_id: uuid.UUID) -> None: ...
