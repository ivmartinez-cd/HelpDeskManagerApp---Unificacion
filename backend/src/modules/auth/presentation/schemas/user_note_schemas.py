from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.auth.domain.entities.user_note import MAX_NOTE_CHARS, UserNote


class UserNoteBody(BaseModel):
    """Tipo y tope en el borde; la misma regla vive en la entidad (fuente de
    verdad) para que valga también fuera de HTTP."""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(max_length=MAX_NOTE_CHARS)


class UserNoteResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content: str
    updated_at: datetime | None = Field(serialization_alias="updatedAt")
    max_chars: int = Field(serialization_alias="maxChars")

    @classmethod
    def from_domain(cls, note: UserNote) -> "UserNoteResponse":
        return cls(content=note.content, updated_at=note.updated_at, max_chars=MAX_NOTE_CHARS)
