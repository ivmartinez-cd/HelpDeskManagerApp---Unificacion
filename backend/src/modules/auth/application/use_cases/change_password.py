import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.auth.domain.errors import InvalidCredentialsError
from src.modules.auth.domain.repositories.session_repository import SessionRepository
from src.modules.auth.domain.repositories.user_repository import UserRepository
from src.modules.auth.domain.services.password_hasher import PasswordHasher
from src.modules.auth.domain.value_objects.raw_password import RawPassword


@dataclass(frozen=True, slots=True)
class ChangePasswordDependencies:
    users: UserRepository
    sessions: SessionRepository
    hasher: PasswordHasher


class ChangePassword:
    def __init__(self, deps: ChangePasswordDependencies) -> None:
        self._deps = deps

    async def execute(
        self,
        *,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
        keep_session_id: uuid.UUID,
    ) -> None:
        user = await self._deps.users.get_by_id(user_id)
        if user is None or not self._deps.hasher.verify(current_password, user.password_hash):
            raise InvalidCredentialsError()
        user.password_hash = self._deps.hasher.hash(RawPassword(new_password))
        await self._deps.users.save(user)
        await self._deps.sessions.revoke_all_for_user(
            user_id, at=datetime.now(UTC), except_session_id=keep_session_id
        )
