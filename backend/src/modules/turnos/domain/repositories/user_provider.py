import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class UserInfo:
    id: uuid.UUID
    full_name: str
    color: str | None = None


class UserProvider(Protocol):
    """Proveedor para obtener información básica de usuarios sin depender de auth."""

    async def get_users_by_ids(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, UserInfo]: ...
    async def list_all_active_users(self) -> list[UserInfo]: ...
