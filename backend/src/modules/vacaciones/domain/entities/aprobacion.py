import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Decision(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(slots=True, eq=False)
class Aprobacion:
    """Entrada del historial de decisiones de una solicitud (ApprovalHistory
    legacy). `approver_user_id` None = el usuario que decidió fue eliminado."""

    id: uuid.UUID
    solicitud_id: uuid.UUID
    approver_user_id: uuid.UUID | None
    decision: Decision
    comment: str | None
    created_at: datetime

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Aprobacion) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
