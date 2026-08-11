"""Vistas de la ventana de validación 0% (request_validations).

PendingValidation es lo que leen el bloqueo 0 de /load y el badge "Validando";
ValidationStart y PendingValidationWork son el lado de escritura/resolución
(ver application/use_cases/validation_window.py)."""

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
    swap_note: str | None = None


@dataclass(frozen=True)
class ValidationStart:
    """Datos con los que arranca (o se completa, si la fila ya existía sin diagnóstico)
    la ventana de validación de una solicitud elegible que llegó en 0%."""

    hp_request_id: int
    customer_id: int
    device_id: int
    device_serial: str
    sku: str
    initial_percent_left: float | None
    deadline_minutes: int
    swap_note: str | None = None
    diagnosis_headline: str | None = None
    diagnosis_detail: str | None = None


@dataclass(frozen=True)
class PendingValidationWork:
    """Fila PENDING tal como la consume resolve_pending: identifica el consumible a
    re-chequear en vivo y trae `is_due` ya calculado contra el reloj de la base (no
    contra la hora local del proceso)."""

    hp_request_id: int
    customer_id: int
    device_id: int
    device_serial: str
    sku: str
    initial_percent_left: float | None
    is_due: bool
