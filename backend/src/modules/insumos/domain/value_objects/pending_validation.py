"""Vista de una validación PENDING (ventana de validación 0%) — lo que el bloqueo 0
de /load necesita para armar el conflicto `pending_validation` del frontend."""

from dataclasses import dataclass
from datetime import datetime

VALIDATION_PENDING = "PENDING"
VALIDATION_CONFIRMED = "CONFIRMED"
VALIDATION_DISMISSED = "DISMISSED"


@dataclass(frozen=True)
class PendingValidation:
    hp_request_id: int
    deadline_at: datetime
    initial_percent_left: float | None = None
    diagnosis_headline: str | None = None
    diagnosis_detail: str | None = None
