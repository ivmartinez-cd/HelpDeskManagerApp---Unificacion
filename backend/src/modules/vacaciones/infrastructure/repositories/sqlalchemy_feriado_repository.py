import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.domain.entities.feriado import Feriado
from src.modules.vacaciones.infrastructure.models.feriado_model import VacacionesFeriadoModel


def _to_entity(row: VacacionesFeriadoModel) -> Feriado:
    return Feriado(
        id=row.id, name=row.name, date=row.date, deducts_vacation=row.deducts_vacation
    )


class SqlAlchemyFeriadoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Feriado]:
        stmt = select(VacacionesFeriadoModel).order_by(VacacionesFeriadoModel.date)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def get_by_id(self, feriado_id: uuid.UUID) -> Feriado | None:
        row = await self._session.get(VacacionesFeriadoModel, feriado_id)
        return _to_entity(row) if row else None

    async def get_by_date(self, fecha: date) -> Feriado | None:
        stmt = select(VacacionesFeriadoModel).where(VacacionesFeriadoModel.date == fecha)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def existe_no_deduce_en(self, fecha: date) -> bool:
        stmt = select(func.count()).where(
            VacacionesFeriadoModel.date == fecha,
            VacacionesFeriadoModel.deducts_vacation.is_(False),
        )
        return (await self._session.execute(stmt)).scalar_one() > 0

    async def upsert_por_fecha(self, feriado: Feriado) -> None:
        stmt = pg_insert(VacacionesFeriadoModel).values(
            id=feriado.id,
            name=feriado.name,
            date=feriado.date,
            deducts_vacation=feriado.deducts_vacation,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[VacacionesFeriadoModel.date],
            set_={"name": feriado.name, "deducts_vacation": feriado.deducts_vacation},
        )
        await self._session.execute(stmt)

    async def add(self, feriado: Feriado) -> None:
        self._session.add(
            VacacionesFeriadoModel(
                id=feriado.id,
                name=feriado.name,
                date=feriado.date,
                deducts_vacation=feriado.deducts_vacation,
            )
        )
        await self._session.flush()

    async def save(self, feriado: Feriado) -> None:
        row = await self._session.get(VacacionesFeriadoModel, feriado.id)
        if row is None:
            return
        row.name = feriado.name
        row.date = feriado.date
        row.deducts_vacation = feriado.deducts_vacation
        await self._session.flush()

    async def delete(self, feriado_id: uuid.UUID) -> None:
        row = await self._session.get(VacacionesFeriadoModel, feriado_id)
        if row is not None:
            await self._session.delete(row)
            await self._session.flush()
