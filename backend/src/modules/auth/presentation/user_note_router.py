from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.application.use_cases.user_note import GetUserNote, SaveUserNote
from src.modules.auth.infrastructure.repositories.sqlalchemy_user_note_repository import (
    SqlAlchemyUserNoteRepository,
)
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.modules.auth.presentation.schemas.user_note_schemas import (
    UserNoteBody,
    UserNoteResponse,
)
from src.shared.infrastructure.database.session import get_db

# /api/me/...: recurso del propio usuario, solo sesión (ADR-033). El
# `user_id` sale siempre de la identidad — nadie lee ni escribe la nota de otro.
router = APIRouter(prefix="/api/me/nota", tags=["me"])


@router.get("")
async def get_nota(
    identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> UserNoteResponse:
    note = await GetUserNote(SqlAlchemyUserNoteRepository(db)).execute(identity.user.id)
    return UserNoteResponse.from_domain(note)


@router.put("")
async def put_nota(
    payload: UserNoteBody,
    identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> UserNoteResponse:
    note = await SaveUserNote(SqlAlchemyUserNoteRepository(db)).execute(
        user_id=identity.user.id, content=payload.content
    )
    return UserNoteResponse.from_domain(note)
