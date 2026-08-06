from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.password_reset_token import PasswordResetToken
from src.modules.auth.infrastructure.models.session_model import PasswordResetToken as ORMToken


class SqlAlchemyResetTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, token: PasswordResetToken) -> None:
        self._session.add(
            ORMToken(
                id=token.id,
                user_id=token.user_id,
                token_hash=token.token_hash,
                expires_at=token.expires_at,
            )
        )
        await self._session.flush()

    async def get_by_token_hash(self, token_hash: bytes) -> PasswordResetToken | None:
        stmt = select(ORMToken).where(ORMToken.token_hash == token_hash)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model else None

    async def mark_used(self, token_hash: bytes, *, at: datetime) -> None:
        stmt = update(ORMToken).where(ORMToken.token_hash == token_hash).values(used_at=at)
        await self._session.execute(stmt)
        await self._session.flush()


def _to_entity(model: ORMToken) -> PasswordResetToken:
    return PasswordResetToken(
        id=model.id,
        user_id=model.user_id,
        token_hash=model.token_hash,
        expires_at=model.expires_at,
        used_at=model.used_at,
    )
