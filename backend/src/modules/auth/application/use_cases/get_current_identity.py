from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.application.mappers import to_identity
from src.modules.auth.domain.entities.session import Session
from src.modules.auth.domain.errors import NotAuthenticatedError
from src.modules.auth.domain.repositories.feature_grant_repository import (
    FeatureGrantRepository,
    FeatureGrantRepositoryNulo,
)
from src.modules.auth.domain.repositories.permission_repository import PermissionRepository
from src.modules.auth.domain.repositories.session_repository import SessionRepository
from src.modules.auth.domain.repositories.user_repository import UserRepository
from src.modules.auth.domain.services.session_token_generator import SessionTokenGenerator

_TOUCH_THRESHOLD = timedelta(hours=1)
_SESSION_TTL = timedelta(days=7)


@dataclass(frozen=True, slots=True)
class GetCurrentIdentityDependencies:
    sessions: SessionRepository
    users: UserRepository
    permissions: PermissionRepository
    tokens: SessionTokenGenerator
    features: FeatureGrantRepository = field(default_factory=FeatureGrantRepositoryNulo)


class GetCurrentIdentity:
    """Backea tanto GET /auth/me como el dependency de FastAPI que protege
    el resto de los endpoints autenticados."""

    def __init__(self, deps: GetCurrentIdentityDependencies) -> None:
        self._deps = deps

    async def execute(self, session_token: str) -> Identity:
        token_hash = self._deps.tokens.hash(session_token)
        session = await self._deps.sessions.get_by_token_hash(token_hash)
        now = datetime.now(UTC)
        if session is None or not session.is_active(at=now):
            raise NotAuthenticatedError()
        user = await self._deps.users.get_by_id(session.user_id)
        if user is None or not user.is_active:
            raise NotAuthenticatedError()
        await self._extend_if_stale(session, now)
        permissions = await self._deps.permissions.get_for_user(user.id)
        features = await self._deps.features.get_for_user(user.id)
        return to_identity(user, permissions, session_id=session.id, features=features)

    async def _extend_if_stale(self, session: Session, now: datetime) -> None:
        """Vencimiento deslizante: solo escribe si pasó más de una hora desde
        el último touch, para no pegarle a la DB en cada request."""
        if now - session.last_seen_at < _TOUCH_THRESHOLD:
            return
        session.last_seen_at = now
        session.expires_at = now + _SESSION_TTL
        await self._deps.sessions.save(session)
