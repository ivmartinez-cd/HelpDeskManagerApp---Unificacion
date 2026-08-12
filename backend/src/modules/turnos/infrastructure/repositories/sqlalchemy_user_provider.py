import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.turnos.domain.repositories.user_provider import UserInfo


class SqlAlchemyUserProvider:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_users_by_ids(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, UserInfo]:
        if not user_ids:
            return {}
        stmt = select(AppUser).where(AppUser.id.in_(user_ids))
        rows = (await self._session.execute(stmt)).scalars().all()
        return {r.id: UserInfo(id=r.id, full_name=r.full_name, color=r.color) for r in rows}

    async def list_all_active_users(self) -> list[UserInfo]:
        stmt = select(AppUser).where(AppUser.is_active.is_(True)).order_by(AppUser.full_name)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [UserInfo(id=r.id, full_name=r.full_name, color=r.color) for r in rows]
