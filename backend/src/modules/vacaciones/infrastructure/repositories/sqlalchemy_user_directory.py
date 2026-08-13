import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.vacaciones.domain.repositories.user_directory import UserInfo


def _to_info(row: AppUser) -> UserInfo:
    return UserInfo(id=row.id, email=row.email, full_name=row.full_name)


class SqlAlchemyUserDirectory:
    """Lectura de cuentas de la plataforma (patrón turnos/UserProvider)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_activos(self) -> list[UserInfo]:
        stmt = select(AppUser).where(AppUser.is_active.is_(True)).order_by(AppUser.full_name)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_info(r) for r in rows]

    async def get_by_id(self, user_id: uuid.UUID) -> UserInfo | None:
        row = await self._session.get(AppUser, user_id)
        return _to_info(row) if row else None

    async def get_by_ids(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, UserInfo]:
        if not user_ids:
            return {}
        stmt = select(AppUser).where(AppUser.id.in_(user_ids))
        rows = (await self._session.execute(stmt)).scalars().all()
        return {r.id: _to_info(r) for r in rows}
