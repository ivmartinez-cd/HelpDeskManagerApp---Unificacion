import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, eq=False)
class Session:
    """Sesión opaca (ADR-004). `is_active`/`revoke` son el invariante central:
    una sesión sirve si no fue revocada y todavía no expiró."""

    id: uuid.UUID
    user_id: uuid.UUID
    token_hash: bytes
    issued_at: datetime
    expires_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None = None
    # Desde dónde se abrió (auditoría / "cerrar otras sesiones").
    ip: str | None = None
    user_agent: str | None = None

    def is_active(self, *, at: datetime) -> bool:
        return self.revoked_at is None and at < self.expires_at

    def revoke(self, *, at: datetime) -> None:
        self.revoked_at = at

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Session) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
