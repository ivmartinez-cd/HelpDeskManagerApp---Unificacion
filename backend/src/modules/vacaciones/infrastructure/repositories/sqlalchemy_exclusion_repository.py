import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.domain.entities.exclusion import Exclusion
from src.modules.vacaciones.infrastructure.models.exclusion_model import (
    VacacionesExclusionModel,
)


def _to_entity(row: VacacionesExclusionModel) -> Exclusion:
    return Exclusion(
        id=row.id, empleado_a_id=row.empleado_a_id, empleado_b_id=row.empleado_b_id
    )


class SqlAlchemyExclusionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Exclusion]:
        rows = (await self._session.execute(select(VacacionesExclusionModel))).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_por_empleado(self, empleado_id: uuid.UUID) -> list[Exclusion]:
        stmt = select(VacacionesExclusionModel).where(
            or_(
                VacacionesExclusionModel.empleado_a_id == empleado_id,
                VacacionesExclusionModel.empleado_b_id == empleado_id,
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def get_by_id(self, exclusion_id: uuid.UUID) -> Exclusion | None:
        row = await self._session.get(VacacionesExclusionModel, exclusion_id)
        return _to_entity(row) if row else None

    async def add(self, exclusion: Exclusion) -> None:
        self._session.add(
            VacacionesExclusionModel(
                id=exclusion.id,
                empleado_a_id=exclusion.empleado_a_id,
                empleado_b_id=exclusion.empleado_b_id,
            )
        )
        await self._session.flush()

    async def delete(self, exclusion_id: uuid.UUID) -> None:
        row = await self._session.get(VacacionesExclusionModel, exclusion_id)
        if row is not None:
            await self._session.delete(row)
            await self._session.flush()
