import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.infrastructure.models.turno_models import TurnoCasillaModel


class SqlAlchemyCasillaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, casilla_id: uuid.UUID) -> Casilla | None:
        model = await self._session.get(TurnoCasillaModel, casilla_id)
        return _to_casilla_entity(model) if model else None

    async def get_by_nombre(self, nombre: str) -> Casilla | None:
        stmt = select(TurnoCasillaModel).where(TurnoCasillaModel.nombre == nombre)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_casilla_entity(model) if model else None

    async def list_all(self, *, include_inactive: bool = False) -> list[Casilla]:
        stmt = select(TurnoCasillaModel)
        if not include_inactive:
            stmt = stmt.where(TurnoCasillaModel.is_active.is_(True))
        stmt = stmt.order_by(TurnoCasillaModel.sort_order, TurnoCasillaModel.nombre)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_casilla_entity(r) for r in rows]

    async def add(self, casilla: Casilla) -> None:
        model = TurnoCasillaModel(
            id=casilla.id,
            nombre=casilla.nombre,
            color=casilla.color,
            sort_order=casilla.sort_order,
            is_active=casilla.is_active,
        )
        self._session.add(model)
        await self._session.flush()

    async def save(self, casilla: Casilla) -> None:
        model = await self._session.get(TurnoCasillaModel, casilla.id)
        if model:
            model.nombre = casilla.nombre
            model.color = casilla.color
            model.sort_order = casilla.sort_order
            model.is_active = casilla.is_active
            await self._session.flush()

    async def delete(self, casilla_id: uuid.UUID) -> None:
        stmt = delete(TurnoCasillaModel).where(TurnoCasillaModel.id == casilla_id)
        await self._session.execute(stmt)
        await self._session.flush()


def _to_casilla_entity(model: TurnoCasillaModel) -> Casilla:
    return Casilla(
        id=model.id,
        nombre=model.nombre,
        color=model.color,
        sort_order=model.sort_order,
        is_active=model.is_active,
    )
