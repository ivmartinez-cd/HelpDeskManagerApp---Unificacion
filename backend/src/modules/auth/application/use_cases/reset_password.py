from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.auth.domain.entities.password_reset_token import PasswordResetToken
from src.modules.auth.domain.errors import (
    AccountDisabledError,
    TokenAlreadyUsedError,
    TokenExpiredError,
    TokenInvalidError,
)
from src.modules.auth.domain.repositories.reset_token_repository import ResetTokenRepository
from src.modules.auth.domain.repositories.session_repository import SessionRepository
from src.modules.auth.domain.repositories.user_repository import UserRepository
from src.modules.auth.domain.services.password_hasher import PasswordHasher
from src.modules.auth.domain.services.session_token_generator import SessionTokenGenerator
from src.modules.auth.domain.value_objects.raw_password import RawPassword


@dataclass(frozen=True, slots=True)
class ResetPasswordDependencies:
    users: UserRepository
    reset_tokens: ResetTokenRepository
    sessions: SessionRepository
    hasher: PasswordHasher
    tokens: SessionTokenGenerator


class ResetPassword:
    def __init__(self, deps: ResetPasswordDependencies) -> None:
        self._deps = deps

    async def execute(self, *, raw_token: str, new_password: str) -> None:
        token_hash = self._deps.tokens.hash(raw_token)
        record = await self._deps.reset_tokens.get_by_token_hash(token_hash)
        now = datetime.now(UTC)
        valid = self._ensure_usable(record, now)
        user = await self._deps.users.get_by_id(valid.user_id)
        if user is None:
            raise TokenInvalidError()
        if not user.is_active:
            raise AccountDisabledError()
        user.password_hash = self._deps.hasher.hash(RawPassword(new_password))
        await self._deps.users.save(user)
        await self._deps.reset_tokens.mark_used(token_hash, at=now)
        # Un password nuevo invalida CUALQUIER sesión abierta con el viejo —
        # a diferencia de change-password, acá no hay "sesión actual" que
        # conservar (este flujo no requiere estar logueado).
        await self._deps.sessions.revoke_all_for_user(user.id, at=now)

    def _ensure_usable(
        self, record: PasswordResetToken | None, now: datetime
    ) -> PasswordResetToken:
        if record is None:
            raise TokenInvalidError()
        if record.used_at is not None:
            raise TokenAlreadyUsedError()
        if not record.is_usable(at=now):
            raise TokenExpiredError()
        return record
