import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from src.modules.auth.application.dtos.commands import LoginCommand
from src.modules.auth.application.dtos.results import AuthenticatedSession
from src.modules.auth.application.mappers import to_identity
from src.modules.auth.domain.entities.session import Session
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.errors import (
    AccountDisabledError,
    InvalidCredentialsError,
    TooManyAttemptsError,
)
from src.modules.auth.domain.repositories.feature_grant_repository import (
    FeatureGrantRepository,
    FeatureGrantRepositoryNulo,
)
from src.modules.auth.domain.repositories.login_attempt_repository import LoginAttemptRepository
from src.modules.auth.domain.repositories.permission_repository import PermissionRepository
from src.modules.auth.domain.repositories.session_repository import SessionRepository
from src.modules.auth.domain.repositories.user_repository import UserRepository
from src.modules.auth.domain.services.password_hasher import PasswordHasher
from src.modules.auth.domain.services.session_token_generator import SessionTokenGenerator
from src.modules.auth.domain.value_objects.email import Email

_MAX_FAILED_ATTEMPTS = 5
_LOCKOUT_WINDOW = timedelta(minutes=15)
_SESSION_TTL = timedelta(days=7)


@dataclass(frozen=True, slots=True)
class AuthenticateUserDependencies:
    users: UserRepository
    sessions: SessionRepository
    permissions: PermissionRepository
    login_attempts: LoginAttemptRepository
    hasher: PasswordHasher
    tokens: SessionTokenGenerator
    features: FeatureGrantRepository = field(default_factory=FeatureGrantRepositoryNulo)


class AuthenticateUser:
    def __init__(self, deps: AuthenticateUserDependencies) -> None:
        self._deps = deps

    async def execute(self, command: LoginCommand) -> AuthenticatedSession:
        await self._guard_rate_limit(command.email)
        user = await self._verify_credentials(command)
        session, token = await self._open_session(user.id)
        permissions = await self._deps.permissions.get_for_user(user.id)
        features = await self._deps.features.get_for_user(user.id)
        identity = to_identity(user, permissions, session_id=session.id, features=features)
        return AuthenticatedSession(identity=identity, session_token=token)

    async def _guard_rate_limit(self, email: str) -> None:
        since = datetime.now(UTC) - _LOCKOUT_WINDOW
        failures = await self._deps.login_attempts.count_recent_failures(email=email, since=since)
        if failures >= _MAX_FAILED_ATTEMPTS:
            retry_after = int(_LOCKOUT_WINDOW.total_seconds())
            raise TooManyAttemptsError(retry_after_seconds=retry_after)

    async def _verify_credentials(self, command: LoginCommand) -> User:
        email = Email(command.email)
        user = await self._deps.users.get_by_email(email)
        password_ok = user is not None and self._deps.hasher.verify(
            command.password, user.password_hash
        )
        # record() comitea internamente (auditoría): sobrevive al 401/403
        # que puede levantarse dos líneas más abajo.
        await self._deps.login_attempts.record(
            email=email.value, ip=command.ip, succeeded=bool(password_ok)
        )
        if not password_ok or user is None:
            raise InvalidCredentialsError()
        if not user.is_active:
            raise AccountDisabledError()
        return user

    async def _open_session(self, user_id: uuid.UUID) -> tuple[Session, str]:
        token = self._deps.tokens.generate()
        now = datetime.now(UTC)
        session = Session(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=self._deps.tokens.hash(token),
            issued_at=now,
            expires_at=now + _SESSION_TTL,
            last_seen_at=now,
        )
        await self._deps.sessions.add(session)
        return session, token
