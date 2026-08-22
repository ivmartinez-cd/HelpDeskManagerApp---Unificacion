from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.dashboard_prefs import DashboardPrefs
from src.modules.auth.infrastructure.models.dashboard_prefs_model import UserDashboardPrefs


class SqlAlchemyDashboardPrefsRepository:
    """Sin commit: el límite transaccional vive en `get_db` (scope="function")."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: UUID) -> DashboardPrefs | None:
        row = await self._session.get(UserDashboardPrefs, user_id)
        return _to_entity(row) if row is not None else None

    async def upsert(self, prefs: DashboardPrefs) -> DashboardPrefs:
        valores = {
            "hidden_cards": list(prefs.hidden_cards),
            "initial_view": prefs.initial_view,
            "updated_at": datetime.now(UTC),
        }
        stmt = pg_insert(UserDashboardPrefs).values(user_id=prefs.user_id, **valores)
        await self._session.execute(
            stmt.on_conflict_do_update(index_elements=[UserDashboardPrefs.user_id], set_=valores)
        )
        return prefs


def _to_entity(row: UserDashboardPrefs) -> DashboardPrefs:
    return DashboardPrefs(
        user_id=row.user_id,
        hidden_cards=tuple(row.hidden_cards),
        initial_view=row.initial_view,
    )
