"""Commands y DTOs de Gestión Humana (empleados, sectores, cargos, feriados)."""

import uuid
from dataclasses import dataclass
from datetime import date

from src.modules.vacaciones.domain.entities.cargo import Cargo
from src.modules.vacaciones.domain.entities.empleado import Empleado, EstadoEmpleado
from src.modules.vacaciones.domain.entities.sector import Sector
from src.modules.vacaciones.domain.repositories.user_directory import UserInfo
from src.modules.vacaciones.domain.value_objects.saldo import Saldo


@dataclass(frozen=True, slots=True)
class EmpleadoCommand:
    first_name: str
    last_name: str
    email: str
    hire_date: date
    department_id: uuid.UUID
    cargo_id: uuid.UUID
    color: str
    status: EstadoEmpleado
    user_id: uuid.UUID | None


@dataclass(frozen=True, slots=True)
class ListEmpleadosQuery:
    search: str | None = None
    department_id: uuid.UUID | None = None
    status: EstadoEmpleado | None = None


@dataclass(frozen=True, slots=True)
class EmpleadoListItemDTO:
    empleado: Empleado
    sector_nombre: str
    sector_color: str
    cargo_nombre: str
    dias_anuales: int
    antiguedad_anios: float
    saldo: Saldo
    """Saldo del año en curso — paridad con `balance` del listado legacy."""
    saldo_siguiente: Saldo | None
    """Solo si el ciclo del año siguiente ya está abierto (paridad con
    `nextYearBalance`, que el legacy solo adjuntaba con `cycleOpen: true`)."""


@dataclass(frozen=True, slots=True)
class SectorCommand:
    name: str
    color: str
    jefe_user_id: uuid.UUID | None


@dataclass(frozen=True, slots=True)
class SectorDTO:
    sector: Sector
    empleados_count: int
    jefes: list[UserInfo]


@dataclass(frozen=True, slots=True)
class CargoCommand:
    name: str
    max_simultaneos: int | None


@dataclass(frozen=True, slots=True)
class CargoDTO:
    cargo: Cargo
    empleados_count: int


@dataclass(frozen=True, slots=True)
class FeriadoCommand:
    name: str
    fecha: date
    deducts_vacation: bool


@dataclass(frozen=True, slots=True)
class ImportFeriadosResultDTO:
    year: int
    count: int
