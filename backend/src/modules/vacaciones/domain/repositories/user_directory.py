import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class UserInfo:
    id: uuid.UUID
    email: str
    full_name: str


class UserDirectory(Protocol):
    """Lectura mínima de cuentas de la plataforma para vincular empleados y
    mostrar jefes/decisores (patrón turnos/UserProvider — la impl vive en
    infrastructure e importa modelos de auth)."""

    async def list_activos(self) -> list[UserInfo]: ...

    async def get_by_id(self, user_id: uuid.UUID) -> UserInfo | None: ...

    async def get_by_ids(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, UserInfo]: ...
