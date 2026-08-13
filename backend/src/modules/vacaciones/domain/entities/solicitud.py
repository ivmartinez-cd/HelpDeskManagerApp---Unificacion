import uuid
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class EstadoSolicitud(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


ESTADOS_ACTIVOS = (EstadoSolicitud.PENDING, EstadoSolicitud.APPROVED)
"""Estados que consumen saldo y bloquean solapamientos (paridad legacy:
las PENDING cuentan igual que las APPROVED)."""


@dataclass(slots=True, eq=False)
class Solicitud:
    """Solicitud de vacaciones. `charged_to_year` None = se imputa al año de
    `start_date` (ver `anio_imputado`)."""

    id: uuid.UUID
    empleado_id: uuid.UUID
    start_date: date
    end_date: date
    days_requested: int
    charged_to_year: int | None
    reason: str | None
    status: EstadoSolicitud
    created_at: datetime

    @property
    def anio_imputado(self) -> int:
        return self.charged_to_year if self.charged_to_year is not None else self.start_date.year

    def solapa_con(self, start: date, end: date) -> bool:
        return self.start_date <= end and start <= self.end_date

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Solicitud) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
