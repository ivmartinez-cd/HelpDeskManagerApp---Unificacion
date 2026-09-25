"""Lectura unificada de personas: ficha de empleado (Gestión de Personal) +
cuenta vinculada (auth). Cruza tablas de ambos módulos a propósito, solo en
infrastructure (ADR-040). Las cuentas placeholder (ex operadores históricos) no
cuentan como acceso."""

import uuid
from typing import Any

from sqlalchemy import ColumnElement, Row, Select, and_, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser, Department
from src.modules.personas.domain.entities.persona import AccesoPersona, DatosPersona, Persona
from src.modules.personas.domain.repositories.persona_repository import (
    FiltrosPersonas,
    OrdenPersonas,
)
from src.modules.vacaciones.infrastructure.models.cargo_model import VacacionesCargoModel
from src.modules.vacaciones.infrastructure.models.empleado_model import VacacionesEmpleadoModel

_E = VacacionesEmpleadoModel
_ACTIVO = "ACTIVE"
_entra = and_(AppUser.id.is_not(None), AppUser.is_active.is_(True))


def _base() -> Select[Any]:
    return (
        select(_E, Department.name, VacacionesCargoModel.name, AppUser)
        .join(Department, Department.id == _E.department_id)
        .join(VacacionesCargoModel, VacacionesCargoModel.id == _E.cargo_id)
        .outerjoin(AppUser, and_(AppUser.id == _E.user_id, AppUser.is_placeholder.is_(False)))
    )


class SqlAlchemyPersonaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_page(
        self, filtros: FiltrosPersonas, orden: OrdenPersonas, *, page: int, size: int
    ) -> tuple[list[Persona], int]:
        stmt = _base().where(*_condiciones(filtros))
        total = await self._session.scalar(select(func.count()).select_from(stmt.subquery()))
        pagina = stmt.order_by(*_clausulas_orden(orden)).offset((page - 1) * size).limit(size)
        rows = (await self._session.execute(pagina)).all()
        return [_to_persona(row) for row in rows], total or 0

    async def get(self, persona_id: uuid.UUID) -> Persona | None:
        row = (await self._session.execute(_base().where(_E.id == persona_id))).first()
        return _to_persona(row) if row else None


def _condiciones(filtros: FiltrosPersonas) -> list[ColumnElement[bool]]:
    condiciones: list[ColumnElement[bool]] = []
    if filtros.busqueda:
        like = f"%{filtros.busqueda.strip()}%"
        nombre = func.concat(_E.first_name, " ", _E.last_name)
        condiciones.append(or_(nombre.ilike(like), _E.email.ilike(like)))
    if filtros.sector_id is not None:
        condiciones.append(_E.department_id == filtros.sector_id)
    if filtros.activa is not None:
        condiciones.append((_E.status == _ACTIVO) if filtros.activa else (_E.status != _ACTIVO))
    if filtros.entra_a_la_app is not None:
        condiciones.append(_entra if filtros.entra_a_la_app else not_(_entra))
    return condiciones


def _clausulas_orden(orden: OrdenPersonas) -> list[ColumnElement[Any]]:
    """Ascendente = como se lee la columna: "Sí" entra a la app antes que "No" y
    "Activa" antes que "Inactiva"."""
    nombre = [func.lower(_E.first_name), func.lower(_E.last_name)]
    columnas: dict[str, tuple[ColumnElement[Any], bool]] = {
        "email": (func.lower(_E.email), False),
        "sector": (func.lower(Department.name), False),
        "cargo": (func.lower(VacacionesCargoModel.name), False),
        "acceso": (func.coalesce(_entra, False), True),
        "estado": (_E.status == _ACTIVO, True),
    }
    if orden.campo not in columnas:
        principales = [c.desc() if orden.descendente else c.asc() for c in nombre]
        return [*principales, _E.id.asc()]
    columna, invertida = columnas[orden.campo]
    principal = columna.desc() if orden.descendente != invertida else columna.asc()
    return [principal, *(c.asc() for c in nombre), _E.id.asc()]


def _to_persona(row: Row[Any]) -> Persona:
    empleado, sector, cargo, cuenta = row
    return Persona(
        id=empleado.id,
        datos=DatosPersona(
            first_name=empleado.first_name,
            last_name=empleado.last_name,
            email=empleado.email,
            color=empleado.color,
        ),
        activa=empleado.status == _ACTIVO,
        sector_id=empleado.department_id,
        sector_nombre=sector,
        cargo_nombre=cargo,
        acceso=_to_acceso(cuenta),
    )


def _to_acceso(cuenta: AppUser | None) -> AccesoPersona | None:
    if cuenta is None:
        return None
    return AccesoPersona(
        user_id=cuenta.id,
        activo=cuenta.is_active,
        superadmin=cuenta.is_superadmin,
        ultimo_ingreso=cuenta.last_login_at,
    )
