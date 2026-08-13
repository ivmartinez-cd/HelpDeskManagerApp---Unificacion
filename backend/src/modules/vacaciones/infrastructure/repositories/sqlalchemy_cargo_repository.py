import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.domain.entities.cargo import Cargo
from src.modules.vacaciones.infrastructure.models.cargo_model import VacacionesCargoModel
from src.modules.vacaciones.infrastructure.models.empleado_model import VacacionesEmpleadoModel


def _to_entity(row: VacacionesCargoModel) -> Cargo:
    return Cargo(id=row.id, name=row.name, max_simultaneos=row.max_simultaneos)


class SqlAlchemyCargoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Cargo]:
        stmt = select(VacacionesCargoModel).order_by(VacacionesCargoModel.name)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def get_by_id(self, cargo_id: uuid.UUID) -> Cargo | None:
        row = await self._session.get(VacacionesCargoModel, cargo_id)
        return _to_entity(row) if row else None

    async def get_by_name(self, name: str) -> Cargo | None:
        stmt = select(VacacionesCargoModel).where(VacacionesCargoModel.name == name)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def count_empleados(self, cargo_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(VacacionesEmpleadoModel.cargo_id == cargo_id)
        return (await self._session.execute(stmt)).scalar_one()

    async def add(self, cargo: Cargo) -> None:
        self._session.add(
            VacacionesCargoModel(
                id=cargo.id, name=cargo.name, max_simultaneos=cargo.max_simultaneos
            )
        )
        await self._session.flush()

    async def save(self, cargo: Cargo) -> None:
        row = await self._session.get(VacacionesCargoModel, cargo.id)
        if row is None:
            return
        row.name = cargo.name
        row.max_simultaneos = cargo.max_simultaneos
        await self._session.flush()

    async def delete(self, cargo_id: uuid.UUID) -> None:
        row = await self._session.get(VacacionesCargoModel, cargo_id)
        if row is not None:
            await self._session.delete(row)
            await self._session.flush()
