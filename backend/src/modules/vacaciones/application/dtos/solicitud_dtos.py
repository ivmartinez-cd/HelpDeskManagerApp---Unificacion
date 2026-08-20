"""Commands y DTOs del core de solicitudes."""

import uuid
from dataclasses import dataclass, field
from datetime import date

from src.modules.vacaciones.domain.entities.aprobacion import Aprobacion
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud, Solicitud


@dataclass(frozen=True, slots=True)
class CrearSolicitudCommand:
    start_date: date
    end_date: date
    empleado_id: uuid.UUID | None = None  # solo admin puede pedir para terceros
    charged_to_year: int | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class EditarSolicitudCommand:
    start_date: date
    end_date: date
    charged_to_year: int | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class DecidirSolicitudCommand:
    decision: str  # 'APPROVED' | 'REJECTED'
    comment: str | None = None


@dataclass(frozen=True, slots=True)
class AfectaTurnosAviso:
    """El empleado aprobado tiene franjas de turno en el rango (ADR-025). No
    crea nada: alimenta el CTA "Armar grilla de cobertura" del frontend."""

    user_id: uuid.UUID
    desde: date
    hasta: date


@dataclass(frozen=True, slots=True)
class DecisionResultado:
    solicitud: Solicitud
    afecta_turnos: AfectaTurnosAviso | None = None


@dataclass(frozen=True, slots=True)
class ListarSolicitudesQuery:
    status: EstadoSolicitud | None = None
    empleado_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    desde: date | None = None
    hasta: date | None = None


@dataclass(frozen=True, slots=True)
class AprobacionDTO:
    aprobacion: Aprobacion
    approver_email: str | None


@dataclass(frozen=True, slots=True)
class SolicitudDTO:
    solicitud: Solicitud
    empleado_nombre: str
    sector_nombre: str
    sector_color: str
    empleado_color: str
    aprobaciones: list[AprobacionDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class SolapamientosDTO:
    overlaps: list[SolicitudDTO]
    team_size: int
