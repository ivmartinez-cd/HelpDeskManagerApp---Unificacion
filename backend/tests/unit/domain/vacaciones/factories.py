"""Factories para los tests de dominio de vacaciones."""

import uuid
from datetime import UTC, date, datetime

from src.modules.vacaciones.domain.entities.empleado import Empleado, EstadoEmpleado
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud, Solicitud
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.modules.vacaciones.domain.value_objects.config_vacaciones import ConfigVacaciones
from src.modules.vacaciones.domain.value_objects.saldo import Saldo
from src.modules.vacaciones.domain.value_objects.seniority_tier import SeniorityTier

TIERS_LEGACY = (
    SeniorityTier(min_years=0, max_years=0.5, days=7),
    SeniorityTier(min_years=0.5, max_years=5, days=14),
    SeniorityTier(min_years=5, max_years=10, days=21),
    SeniorityTier(min_years=10, max_years=20, days=28),
    SeniorityTier(min_years=20, max_years=99, days=35),
)


def make_config(**overrides: object) -> ConfigVacaciones:
    defaults: dict[str, object] = {
        "seniority_tiers": TIERS_LEGACY,
        "next_year_open_month": 10,
        "next_year_open_day": 1,
        "allow_advance_request": True,
        "max_advance_days": 0,
        "allow_carry_over": True,
        "max_carry_over_days": 0,
    }
    defaults.update(overrides)
    return ConfigVacaciones(**defaults)  # type: ignore[arg-type]


def make_empleado(**overrides: object) -> Empleado:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "first_name": "Laura",
        "last_name": "Pérez",
        "email": "lperez@canal.com",
        "hire_date": date(2019, 3, 15),
        "annual_vacation_days": 22,
        "status": EstadoEmpleado.ACTIVE,
        "color": "#2563eb",
        "department_id": uuid.uuid4(),
        "cargo_id": uuid.uuid4(),
        "user_id": None,
    }
    defaults.update(overrides)
    return Empleado(**defaults)  # type: ignore[arg-type]


def make_solicitud(**overrides: object) -> Solicitud:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "empleado_id": uuid.uuid4(),
        "start_date": date(2026, 8, 3),
        "end_date": date(2026, 8, 13),
        "days_requested": 10,
        "charged_to_year": 2026,
        "reason": None,
        "status": EstadoSolicitud.PENDING,
        "created_at": datetime(2026, 8, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return Solicitud(**defaults)  # type: ignore[arg-type]


def make_saldo(**overrides: object) -> Saldo:
    defaults: dict[str, object] = {
        "annual": 14,
        "carry_over": 0,
        "used": 0,
        "pending": 0,
        "available": 14,
        "cycle_open": True,
    }
    defaults.update(overrides)
    return Saldo(**defaults)  # type: ignore[arg-type]


def make_actor(**overrides: object) -> ActorVacaciones:
    defaults: dict[str, object] = {
        "user_id": uuid.uuid4(),
        "es_admin": False,
        "sector_gestionado_id": None,
        "empleado_id": None,
    }
    defaults.update(overrides)
    return ActorVacaciones(**defaults)  # type: ignore[arg-type]
