from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.user_note import UserNote
from src.modules.auth.infrastructure.models.user_note_model import UserNoteModel


class SqlAlchemyUserNoteRepository:
    """Sin commit: el límite transaccional vive en `get_db` (scope="function")."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: UUID) -> UserNote | None:
        row = await self._session.get(UserNoteModel, user_id)
        if row is None:
            return None
        return UserNote(user_id=row.user_id, content=row.content, updated_at=row.updated_at)

    async def upsert(self, note: UserNote) -> UserNote:
        ahora = datetime.now(UTC)
        valores = {"content": note.content, "updated_at": ahora}
        stmt = pg_insert(UserNoteModel).values(user_id=note.user_id, **valores)
        await self._session.execute(
            stmt.on_conflict_do_update(index_elements=[UserNoteModel.user_id], set_=valores)
        )
        return UserNote(user_id=note.user_id, content=note.content, updated_at=ahora)
