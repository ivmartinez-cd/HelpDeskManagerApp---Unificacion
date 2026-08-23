from typing import Protocol
from uuid import UUID

from src.modules.auth.domain.entities.user_note import UserNote


class UserNoteRepository(Protocol):
    async def get(self, user_id: UUID) -> UserNote | None: ...

    async def upsert(self, note: UserNote) -> UserNote: ...
