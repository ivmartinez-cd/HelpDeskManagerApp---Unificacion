"""DTOs de dashboard, calendario y ciclos."""

import uuid
from dataclasses import dataclass
from datetime import date

from src.modules.vacaciones.domain.entities.ciclo import Ciclo
from src.modules.vacaciones.domain.value_objects.saldo import Saldo


@dataclass(frozen=True, slots=True)
class EventoCalendarioDTO:
    id: str
    titulo: str
    start: date
    end_exclusivo: date  # convención de calendario: fin exclusivo (legacy +1 día)
    tipo: str  # 'vacation' | 'holiday'
    color: str
    border_color: str | None
    status: str | None
    empleado: str | None
    sector: str | None
    dias: int | None
    restantes: int | None
    reason: str | None


@dataclass(frozen=True, slots=True)
class DiasDTO:
    saldo: Saldo | None
    year: int


@dataclass(frozen=True, slots=True)
class EnVacacionesDTO:
    solicitud_id: uuid.UUID
    empleado_nombre: str
    empleado_color: str
    sector_nombre: str
    sector_color: str
    start_date: date
    end_date: date


@dataclass(frozen=True, slots=True)
class DashboardResumenDTO:
    total_empleados: int
    empleados_activos: int
    solicitudes_pendientes: int
    en_vacaciones: list[EnVacacionesDTO]
    dias: DiasDTO | None
    dias_proximo: DiasDTO | None
    dias_totales_equipo: int | None  # solo admin: suma de annual+carry del equipo
    dias_disponibles_equipo: int | None


@dataclass(frozen=True, slots=True)
class CicloDTO:
    ciclo: Ciclo
    empleado_nombre: str


@dataclass(frozen=True, slots=True)
class AbrirCiclosResultDTO:
    opened: int
    skipped: int
