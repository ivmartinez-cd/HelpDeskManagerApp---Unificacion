from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.modules.auth.domain.errors import NoteTooLongError

# Tope de la nota (caracteres). El backend es la fuente de verdad; el
# frontend lo espeja en el contador del textarea.
MAX_NOTE_CHARS = 4000


@dataclass(frozen=True, slots=True)
class UserNote:
    """Nota personal (scratchpad) del usuario en Inicio: texto libre, una por
    usuario, privada. Se guarda completa en cada PUT (debounce en el cliente,
    nunca por tecla — ver docs/MASTER_PROMPT_NOTA_PERSONAL_INICIO.md)."""

    user_id: UUID
    content: str
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if len(self.content) > MAX_NOTE_CHARS:
            raise NoteTooLongError(len(self.content), MAX_NOTE_CHARS)

    @classmethod
    def empty(cls, user_id: UUID) -> "UserNote":
        return cls(user_id=user_id, content="", updated_at=None)
