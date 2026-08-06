from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.auth.domain.repositories.session_repository import SessionRepository
from src.modules.auth.domain.services.session_token_generator import SessionTokenGenerator


@dataclass(frozen=True, slots=True)
class RevokeSessionDependencies:
    sessions: SessionRepository
    tokens: SessionTokenGenerator


class RevokeSession:
    def __init__(self, deps: RevokeSessionDependencies) -> None:
        self._deps = deps

    async def execute(self, session_token: str) -> None:
        token_hash = self._deps.tokens.hash(session_token)
        session = await self._deps.sessions.get_by_token_hash(token_hash)
        if session is None:
            return
        session.revoke(at=datetime.now(UTC))
        await self._deps.sessions.save(session)
