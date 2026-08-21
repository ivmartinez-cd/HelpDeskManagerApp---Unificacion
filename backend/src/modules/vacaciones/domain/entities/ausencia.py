import uuid
from dataclasses import dataclass
from datetime import date, datetime, time
from enum import StrEnum

from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud


class TipoAusencia(StrEnum):
    DESCUENTO_DIA = "DESCUENTO_DIA"
    BAJA_ENFERMEDAD = "BAJA_ENFERMEDAD"
    TRAMITE_PERSONAL = "TRAMITE_PERSONAL"
    GUARDIA = "GUARDIA"
    DIA_ESTUDIO = "DIA_ESTUDIO"
    HOME_OFFICE = "HOME_OFFICE"
    # Horario distinto al habitual por un rango de días (ej. 8-17 en vez de
    # 9-18): lleva `hora_desde`/`hora_hasta`. No es una ausencia del día:
    # el operador trabaja, pero Turnos tiene que saber en qué ventana.
    CAMBIO_HORARIO = "CAMBIO_HORARIO"
    OTHER = "OTHER"


TIPOS_SOLICITABLES = (TipoAusencia.HOME_OFFICE, TipoAusencia.CAMBIO_HORARIO)
"""Lo que un empleado pide desde "Solicitudes" y la TL aprueba (2026-08-21)."""


@dataclass(slots=True, eq=False)
class Ausencia:
    """Baja/ausencia (Absence del legacy). Las que carga un admin/jefe nacen
    APPROVED; las que pide un empleado para sí nacen PENDING y las decide quien
    tiene `approve` (mismo circuito que las vacaciones). `days_count` usa el
    mismo conteo corrido con extensión LCT que las solicitudes, y `half_day`
    hace que compute 0.5 en los reportes sin alterar `days_count`.
    `hora_desde`/`hora_hasta` solo aplican a CAMBIO_HORARIO.
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
    hora_desde: time | None = None
    hora_hasta: time | None = None

    @property
    def dias_computados(self) -> float:
        return 0.5 if self.half_day else float(self.days_count)

    @property
    def horario_texto(self) -> str | None:
        """'08:00–17:00' para CAMBIO_HORARIO; None para el resto."""
        if self.hora_desde is None or self.hora_hasta is None:
            return None
        return f"{self.hora_desde:%H:%M}–{self.hora_hasta:%H:%M}"

    def cubre(self, dia: date) -> bool:
        return self.start_date <= dia <= self.end_date

    def solapa_con(self, start: date, end: date) -> bool:
        return self.start_date <= end and start <= self.end_date

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Ausencia) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
