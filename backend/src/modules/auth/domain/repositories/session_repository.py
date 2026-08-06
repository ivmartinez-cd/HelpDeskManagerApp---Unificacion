import uuid
from datetime import datetime
from typing import Protocol

from src.modules.auth.domain.entities.session import Session


class SessionRepository(Protocol):
    async def get_by_token_hash(self, token_hash: bytes) -> Session | None: ...
    async def add(self, session: Session) -> None: ...
    async def save(self, session: Session) -> None: ...
    async def revoke_all_for_user(
        self, user_id: uuid.UUID, *, at: datetime, except_session_id: uuid.UUID | None = None
    ) -> None: ...
