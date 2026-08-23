import uuid

import pytest

from src.modules.auth.domain.entities.user_note import MAX_NOTE_CHARS, UserNote
from src.modules.auth.domain.errors import NoteTooLongError


def test_empty_es_texto_vacio_sin_fecha() -> None:
    note = UserNote.empty(uuid.uuid4())

    assert (note.content, note.updated_at) == ("", None)


def test_acepta_hasta_el_tope_exacto() -> None:
    note = UserNote(user_id=uuid.uuid4(), content="x" * MAX_NOTE_CHARS)

    assert len(note.content) == MAX_NOTE_CHARS


def test_rechaza_por_encima_del_tope_con_error_de_dominio() -> None:
    with pytest.raises(NoteTooLongError, match=str(MAX_NOTE_CHARS)):
        UserNote(user_id=uuid.uuid4(), content="x" * (MAX_NOTE_CHARS + 1))
