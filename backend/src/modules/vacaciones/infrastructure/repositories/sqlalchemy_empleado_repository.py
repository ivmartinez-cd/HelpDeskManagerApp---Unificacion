import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.domain.entities.empleado import Empleado, EstadoEmpleado
from src.modules.vacaciones.domain.errors import SigesVinculoDuplicadoError
from src.modules.vacaciones.domain.repositories.empleado_repository import FiltrosEmpleados
from src.modules.vacaciones.infrastructure.models.cargo_model import VacacionesCargoModel
from src.modules.vacaciones.infrastructure.models.empleado_model import VacacionesEmpleadoModel


def _to_entity(row: VacacionesEmpleadoModel) -> Empleado:
    return Empleado(
        id=row.id,
        first_name=row.first_name,
        last_name=row.last_name,
        email=row.email,
        hire_date=row.hire_date,
        annual_vacation_days=row.annual_vacation_days,
        status=EstadoEmpleado(row.status),
        color=row.color,
        department_id=row.department_id,
        cargo_id=row.cargo_id,
        user_id=row.user_id,
        siges_empresa_id=row.siges_empresa_id,
    )


class SqlAlchemyEmpleadoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, empleado_id: uuid.UUID) -> Empleado | None:
        row = await self._session.get(VacacionesEmpleadoModel, empleado_id)
        return _to_entity(row) if row else None

    async def get_by_user_id(self, user_id: uuid.UUID) -> Empleado | None:
        stmt = select(VacacionesEmpleadoModel).where(VacacionesEmpleadoModel.user_id == user_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def get_by_email(self, email: str) -> Empleado | None:
        stmt = select(VacacionesEmpleadoModel).where(VacacionesEmpleadoModel.email == email)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def get_by_ids(
        self, empleado_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, Empleado]:
        if not empleado_ids:
            return {}
        stmt = select(VacacionesEmpleadoModel).where(
            VacacionesEmpleadoModel.id.in_(empleado_ids)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return {r.id: _to_entity(r) for r in rows}

    async def list_filtrados(self, filtros: FiltrosEmpleados) -> list[Empleado]:
        stmt = select(VacacionesEmpleadoModel).order_by(
            VacacionesEmpleadoModel.last_name, VacacionesEmpleadoModel.first_name
        )
        if filtros.search:
            patron = f"%{filtros.search}%"
            stmt = stmt.join(
                VacacionesCargoModel,
                VacacionesCargoModel.id == VacacionesEmpleadoModel.cargo_id,
            ).where(
                or_(
                    VacacionesEmpleadoModel.first_name.ilike(patron),
                    VacacionesEmpleadoModel.last_name.ilike(patron),
                    VacacionesEmpleadoModel.email.ilike(patron),
                    VacacionesCargoModel.name.ilike(patron),
                )
            )
        if filtros.department_id is not None:
            stmt = stmt.where(VacacionesEmpleadoModel.department_id == filtros.department_id)
        if filtros.status is not None:
            stmt = stmt.where(VacacionesEmpleadoModel.status == filtros.status.value)
        if filtros.empleado_id is not None:
            stmt = stmt.where(VacacionesEmpleadoModel.id == filtros.empleado_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def count_activos_por_departamento(self, department_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(
            VacacionesEmpleadoModel.department_id == department_id,
            VacacionesEmpleadoModel.status == EstadoEmpleado.ACTIVE.value,
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def add(self, empleado: Empleado) -> None:
        self._session.add(_to_model(empleado))
        await self._session.flush()

    async def save(self, empleado: Empleado) -> None:
        row = await self._session.get(VacacionesEmpleadoModel, empleado.id)
        if row is None:
            return
        _apply(row, empleado)
        await self._session.flush()

    async def delete(self, empleado_id: uuid.UUID) -> None:
        row = await self._session.get(VacacionesEmpleadoModel, empleado_id)
        if row is not None:
            await self._session.delete(row)
            await self._session.flush()

    async def vincular_siges(
        self, empleado_id: uuid.UUID, *, siges_empresa_id: int | None
    ) -> Empleado | None:
        row = await self._session.get(VacacionesEmpleadoModel, empleado_id)
        if row is None:
            return None
        row.siges_empresa_id = siges_empresa_id
        # flush() explícito para atrapar acá la violación del UNIQUE (mismo
        # criterio que liquidaciones): un técnico de Siges vincula a lo sumo
        # un empleado.
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise SigesVinculoDuplicadoError(siges_empresa_id) from exc
        await self._session.refresh(row)
        return _to_entity(row)


def _to_model(empleado: Empleado) -> VacacionesEmpleadoModel:
    row = VacacionesEmpleadoModel(id=empleado.id)
    _apply(row, empleado)
    return row


def _apply(row: VacacionesEmpleadoModel, empleado: Empleado) -> None:
    row.first_name = empleado.first_name
    row.last_name = empleado.last_name
    row.email = empleado.email
    row.hire_date = empleado.hire_date
    row.annual_vacation_days = empleado.annual_vacation_days
    row.status = empleado.status.value
    row.color = empleado.color
    row.department_id = empleado.department_id
    row.cargo_id = empleado.cargo_id
    row.user_id = empleado.user_id
    row.siges_empresa_id = empleado.siges_empresa_id
