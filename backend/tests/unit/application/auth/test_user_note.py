import uuid
from uuid import UUID

import pytest

from src.modules.auth.application.use_cases.user_note import GetUserNote, SaveUserNote
from src.modules.auth.domain.entities.user_note import MAX_NOTE_CHARS, UserNote
from src.modules.auth.domain.errors import NoteTooLongError


class FakeUserNoteRepository:
    def __init__(self) -> None:
        self.rows: dict[UUID, UserNote] = {}

    async def get(self, user_id: UUID) -> UserNote | None:
        return self.rows.get(user_id)

    async def upsert(self, note: UserNote) -> UserNote:
        self.rows[note.user_id] = note
        return note


async def test_get_devuelve_nota_vacia_si_nunca_escribio() -> None:
    user_id = uuid.uuid4()

    note = await GetUserNote(FakeUserNoteRepository()).execute(user_id)

    assert note == UserNote.empty(user_id)


async def test_save_pisa_el_contenido_y_no_mezcla_usuarios() -> None:
    repo = FakeUserNoteRepository()
    a, b = uuid.uuid4(), uuid.uuid4()

    await SaveUserNote(repo).execute(user_id=a, content="primera")
    await SaveUserNote(repo).execute(user_id=a, content="segunda")

    assert (await GetUserNote(repo).execute(a)).content == "segunda"
    assert (await GetUserNote(repo).execute(b)).content == ""


async def test_save_rechaza_exceso_antes_de_persistir() -> None:
    repo = FakeUserNoteRepository()

    with pytest.raises(NoteTooLongError):
        await SaveUserNote(repo).execute(user_id=uuid.uuid4(), content="x" * (MAX_NOTE_CHARS + 1))
    assert repo.rows == {}
