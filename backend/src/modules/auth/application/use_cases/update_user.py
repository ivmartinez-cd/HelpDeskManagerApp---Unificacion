import uuid
from dataclasses import dataclass

from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.errors import LastSuperadminError, UserNotFoundError
from src.modules.auth.domain.repositories.user_repository import UserRepository


@dataclass(frozen=True, slots=True)
class UpdateUserDependencies:
    users: UserRepository


class UpdateUser:
    def __init__(self, deps: UpdateUserDependencies) -> None:
        self._deps = deps

    async def execute(
        self,
        *,
        user_id: uuid.UUID,
        full_name: str | None,
        is_active: bool | None,
        color: str | None = None,
    ) -> User:
        user = await self._deps.users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        if is_active is False and user.is_superadmin:
            await self._guard_last_superadmin()
        if full_name is not None:
            user.full_name = full_name
        if is_active is not None:
            user.is_active = is_active
        if color is not None:
            user.color = color
        await self._deps.users.save(user)
        return user

    async def _guard_last_superadmin(self) -> None:
        if await self._deps.users.count_active_superadmins() <= 1:
            raise LastSuperadminError()
