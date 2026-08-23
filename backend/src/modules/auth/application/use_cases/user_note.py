from uuid import UUID

from src.modules.auth.domain.entities.user_note import UserNote
from src.modules.auth.domain.repositories.user_note_repository import UserNoteRepository


class GetUserNote:
    """Nota personal del usuario logueado; vacía si nunca escribió."""

    def __init__(self, repo: UserNoteRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID) -> UserNote:
        return await self._repo.get(user_id) or UserNote.empty(user_id)


class SaveUserNote:
    """Reemplaza el contenido completo (PUT idempotente). El `user_id` viene
    siempre de la identidad de la sesión; el tope de longitud lo valida la
    entidad (error de dominio → 400, nunca 500)."""

    def __init__(self, repo: UserNoteRepository) -> None:
        self._repo = repo

    async def execute(self, *, user_id: UUID, content: str) -> UserNote:
        return await self._repo.upsert(UserNote(user_id=user_id, content=content))
