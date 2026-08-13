import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import Department
from src.modules.vacaciones.domain.entities.sector import Sector


def _to_entity(row: Department) -> Sector:
    return Sector(id=row.id, name=row.name, color=row.color, is_active=row.is_active)


class SqlAlchemySectorRepository:
    """ABM de Sectores sobre la tabla `department` compartida con auth (D1).
    Importa el modelo de auth desde infrastructure — permitido por los
    contratos de importlinter (solo domain/application lo tienen prohibido).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Sector]:
        stmt = select(Department).order_by(Department.name)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def get_by_id(self, sector_id: uuid.UUID) -> Sector | None:
        row = await self._session.get(Department, sector_id)
        return _to_entity(row) if row else None

    async def get_by_name(self, name: str) -> Sector | None:
        stmt = select(Department).where(Department.name == name)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def add(self, sector: Sector) -> None:
        self._session.add(
            Department(
                id=sector.id, name=sector.name, color=sector.color, is_active=sector.is_active
            )
        )
        await self._session.flush()

    async def save(self, sector: Sector) -> None:
        row = await self._session.get(Department, sector.id)
        if row is None:
            return
        row.name = sector.name
        row.color = sector.color
        row.is_active = sector.is_active
        await self._session.flush()

    async def delete(self, sector_id: uuid.UUID) -> None:
        row = await self._session.get(Department, sector_id)
        if row is not None:
            await self._session.delete(row)
            await self._session.flush()
