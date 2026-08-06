import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, eq=False)
class PasswordResetToken:
    id: uuid.UUID
    user_id: uuid.UUID
    token_hash: bytes
    expires_at: datetime
    used_at: datetime | None = None

    def is_usable(self, *, at: datetime) -> bool:
        return self.used_at is None and at < self.expires_at

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PasswordResetToken) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
