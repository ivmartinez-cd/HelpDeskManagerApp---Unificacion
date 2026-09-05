import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.session import Session
from src.modules.auth.infrastructure.models.session_model import UserSession


class SqlAlchemySessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_token_hash(self, token_hash: bytes) -> Session | None:
        stmt = select(UserSession).where(UserSession.token_hash == token_hash)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model else None

    async def add(self, session: Session) -> None:
        self._session.add(_to_new_model(session))
        await self._session.flush()

    async def save(self, session: Session) -> None:
        model = await self._session.get(UserSession, session.id)
        if model is None:
            raise LookupError(f"Session {session.id} no existe")
        model.last_seen_at = session.last_seen_at
        model.expires_at = session.expires_at
        model.revoked_at = session.revoked_at
        await self._session.flush()

    async def revoke_all_for_user(
        self, user_id: uuid.UUID, *, at: datetime, except_session_id: uuid.UUID | None = None
    ) -> None:
        conditions = [UserSession.user_id == user_id, UserSession.revoked_at.is_(None)]
        if except_session_id is not None:
            conditions.append(UserSession.id != except_session_id)
        stmt = update(UserSession).where(*conditions).values(revoked_at=at)
        await self._session.execute(stmt)
        await self._session.flush()


def _to_entity(model: UserSession) -> Session:
    return Session(
        id=model.id,
        user_id=model.user_id,
        token_hash=model.token_hash,
        issued_at=model.issued_at,
        expires_at=model.expires_at,
        last_seen_at=model.last_seen_at,
        revoked_at=model.revoked_at,
        ip=model.ip,
        user_agent=model.user_agent,
    )


def _to_new_model(session: Session) -> UserSession:
    return UserSession(
        id=session.id,
        user_id=session.user_id,
        token_hash=session.token_hash,
        expires_at=session.expires_at,
        ip=session.ip,
        user_agent=session.user_agent,
    )
