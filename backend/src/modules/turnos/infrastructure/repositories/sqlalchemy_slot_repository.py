import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.infrastructure.models.turno_models import TurnoSlotModel


class SqlAlchemySlotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, slot_id: uuid.UUID) -> Slot | None:
        model = await self._session.get(TurnoSlotModel, slot_id)
        return _to_slot_entity(model) if model else None

    async def list_by_casilla(self, casilla_id: uuid.UUID) -> list[Slot]:
        stmt = (
            select(TurnoSlotModel)
            .where(TurnoSlotModel.casilla_id == casilla_id)
            .order_by(TurnoSlotModel.dia_semana, TurnoSlotModel.hora_inicio)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_slot_entity(r) for r in rows]

    async def list_all(self) -> list[Slot]:
        stmt = select(TurnoSlotModel).order_by(
            TurnoSlotModel.dia_semana, TurnoSlotModel.hora_inicio
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_slot_entity(r) for r in rows]

    async def add(self, slot: Slot) -> None:
        model = TurnoSlotModel(
            id=slot.id,
            casilla_id=slot.casilla_id,
            hora_inicio=slot.hora_inicio,
            hora_fin=slot.hora_fin,
            dia_semana=slot.dia_semana,
            sort_order=slot.sort_order,
        )
        self._session.add(model)
        await self._session.flush()

    async def save(self, slot: Slot) -> None:
        model = await self._session.get(TurnoSlotModel, slot.id)
        if model:
            model.hora_inicio = slot.hora_inicio
            model.hora_fin = slot.hora_fin
            model.dia_semana = slot.dia_semana
            model.sort_order = slot.sort_order
            await self._session.flush()

    async def delete(self, slot_id: uuid.UUID) -> None:
        await self._session.execute(delete(TurnoSlotModel).where(TurnoSlotModel.id == slot_id))
        await self._session.flush()


def _to_slot_entity(model: TurnoSlotModel) -> Slot:
    return Slot(
        id=model.id,
        casilla_id=model.casilla_id,
        hora_inicio=model.hora_inicio,
        hora_fin=model.hora_fin,
        dia_semana=model.dia_semana,
        sort_order=model.sort_order,
    )
