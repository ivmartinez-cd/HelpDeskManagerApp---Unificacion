import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.domain.entities.ciclo import Ciclo
from src.modules.vacaciones.infrastructure.models.ciclo_model import VacacionesCicloModel


def _to_entity(row: VacacionesCicloModel) -> Ciclo:
    return Ciclo(
        id=row.id,
        empleado_id=row.empleado_id,
        year=row.year,
        annual_days=row.annual_days,
        carry_over=row.carry_over,
        is_open=row.is_open,
        opened_at=row.opened_at,
    )


class SqlAlchemyCicloRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, empleado_id: uuid.UUID, year: int) -> Ciclo | None:
        stmt = select(VacacionesCicloModel).where(
            VacacionesCicloModel.empleado_id == empleado_id,
            VacacionesCicloModel.year == year,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def list_por_empleado(self, empleado_id: uuid.UUID) -> list[Ciclo]:
        stmt = (
            select(VacacionesCicloModel)
            .where(VacacionesCicloModel.empleado_id == empleado_id)
            .order_by(VacacionesCicloModel.year)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_por_empleados(self, empleado_ids: list[uuid.UUID]) -> list[Ciclo]:
        if not empleado_ids:
            return []
        stmt = select(VacacionesCicloModel).where(
            VacacionesCicloModel.empleado_id.in_(empleado_ids)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_por_year(self, year: int) -> list[Ciclo]:
        stmt = select(VacacionesCicloModel).where(VacacionesCicloModel.year == year)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def add(self, ciclo: Ciclo) -> None:
        self._session.add(
            VacacionesCicloModel(
                id=ciclo.id,
                empleado_id=ciclo.empleado_id,
                year=ciclo.year,
                annual_days=ciclo.annual_days,
                carry_over=ciclo.carry_over,
                is_open=ciclo.is_open,
                opened_at=ciclo.opened_at,
            )
        )
        await self._session.flush()

    async def save(self, ciclo: Ciclo) -> None:
        row = await self._session.get(VacacionesCicloModel, ciclo.id)
        if row is None:
            return
        row.annual_days = ciclo.annual_days
        row.carry_over = ciclo.carry_over
        row.is_open = ciclo.is_open
        row.opened_at = ciclo.opened_at
        await self._session.flush()
