import uuid
from dataclasses import dataclass
from datetime import datetime

from src.modules.auth.domain.value_objects.email import Email
from src.modules.auth.domain.value_objects.password_hash import PasswordHash


@dataclass(slots=True, eq=False)
class User:
    """Entidad: la identidad es `id`, no la igualdad estructural de campos."""

    id: uuid.UUID
    email: Email
    password_hash: PasswordHash
    full_name: str
    is_active: bool
    is_superadmin: bool
    created_at: datetime
    last_login_at: datetime | None = None

    def __eq__(self, other: object) -> bool:
        return isinstance(other, User) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
