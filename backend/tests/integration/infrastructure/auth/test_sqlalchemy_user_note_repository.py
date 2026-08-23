"""SqlAlchemyUserNoteRepository contra Postgres real (upsert por user_id)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.user_note import UserNote
from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.auth.infrastructure.repositories.sqlalchemy_user_note_repository import (
    SqlAlchemyUserNoteRepository,
)


async def _crear_usuario(db_session: AsyncSession) -> uuid.UUID:
    user = AppUser(
        email=f"{uuid.uuid4()}@test.local", full_name="Nota Test", password_hash="x",
        is_superadmin=False,
    )
    db_session.add(user)
    await db_session.flush()
    return user.id


async def test_get_sin_fila_devuelve_none(db_session: AsyncSession) -> None:
    assert await SqlAlchemyUserNoteRepository(db_session).get(uuid.uuid4()) is None


async def test_upsert_inserta_pisa_y_devuelve_fecha(db_session: AsyncSession) -> None:
    user_id = await _crear_usuario(db_session)
    repo = SqlAlchemyUserNoteRepository(db_session)

    await repo.upsert(UserNote(user_id=user_id, content="hola"))
    guardada = await repo.upsert(UserNote(user_id=user_id, content="hola de nuevo"))
    leida = await repo.get(user_id)

    assert guardada.updated_at is not None
    assert leida is not None and leida.content == "hola de nuevo"
    assert leida.updated_at is not None


async def test_la_nota_es_por_usuario(db_session: AsyncSession) -> None:
    a = await _crear_usuario(db_session)
    b = await _crear_usuario(db_session)
    repo = SqlAlchemyUserNoteRepository(db_session)

    await repo.upsert(UserNote(user_id=a, content="privada de a"))

    assert await repo.get(b) is None
