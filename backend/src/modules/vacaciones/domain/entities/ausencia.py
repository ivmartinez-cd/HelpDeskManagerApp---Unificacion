import uuid
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud


class TipoAusencia(StrEnum):
    DESCUENTO_DIA = "DESCUENTO_DIA"
    BAJA_ENFERMEDAD = "BAJA_ENFERMEDAD"
    TRAMITE_PERSONAL = "TRAMITE_PERSONAL"
    GUARDIA = "GUARDIA"
    DIA_ESTUDIO = "DIA_ESTUDIO"
    HOME_OFFICE = "HOME_OFFICE"
    OTHER = "OTHER"


@dataclass(slots=True, eq=False)
class Ausencia:
    """Baja/ausencia (Absence del legacy). Nace APPROVED (a diferencia de las
    solicitudes de vacaciones no pasa por aprobación); `days_count` usa el
    mismo conteo corrido con extensión LCT que las solicitudes, y `half_day`
    hace que compute 0.5 en los reportes sin alterar `days_count`.
    """

    id: uuid.UUID
    empleado_id: uuid.UUID
    start_date: date
    end_date: date
    days_count: int
    half_day: bool
    tipo: TipoAusencia
    reason: str | None
    status: EstadoSolicitud
    created_at: datetime

    @property
    def dias_computados(self) -> float:
        return 0.5 if self.half_day else float(self.days_count)

    def cubre(self, dia: date) -> bool:
        return self.start_date <= dia <= self.end_date

    def solapa_con(self, start: date, end: date) -> bool:
        return self.start_date <= end and start <= self.end_date

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Ausencia) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
