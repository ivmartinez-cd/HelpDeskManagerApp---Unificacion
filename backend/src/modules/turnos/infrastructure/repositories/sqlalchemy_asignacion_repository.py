import uuid
from datetime import date, timedelta

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.infrastructure.models.turno_models import TurnoAsignacionModel

_ONE_DAY = timedelta(days=1)


class SqlAlchemyAsignacionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_slots(
        self, slot_ids: list[uuid.UUID], target_date: date
    ) -> dict[uuid.UUID, list[Asignacion]]:
        if not slot_ids:
            return {}
        stmt = select(TurnoAsignacionModel).where(
            TurnoAsignacionModel.slot_id.in_(slot_ids),
            TurnoAsignacionModel.vigente_desde <= target_date,
            or_(
                TurnoAsignacionModel.vigente_hasta.is_(None),
                TurnoAsignacionModel.vigente_hasta >= target_date,
            ),
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        grouped: dict[uuid.UUID, list[Asignacion]] = {}
        for r in rows:
            grouped.setdefault(r.slot_id, []).append(_to_asignacion_entity(r))
        return grouped

    async def list_active_on_date(self, target_date: date) -> list[Asignacion]:
        stmt = select(TurnoAsignacionModel).where(
            TurnoAsignacionModel.vigente_desde <= target_date,
            or_(
                TurnoAsignacionModel.vigente_hasta.is_(None),
                TurnoAsignacionModel.vigente_hasta >= target_date,
            ),
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_asignacion_entity(r) for r in rows]

    async def replace_for_slot(
        self, slot_id: uuid.UUID, effective_date: date, asignaciones: list[Asignacion]
    ) -> None:
        close_at = effective_date - _ONE_DAY
        stmt = select(TurnoAsignacionModel).where(
            TurnoAsignacionModel.slot_id == slot_id,
            TurnoAsignacionModel.vigente_hasta.is_(None),
        )
        open_rows = (await self._session.execute(stmt)).scalars().all()
        for row in open_rows:
            if row.vigente_desde > close_at:
                # Cerrarla dejaría vigente_hasta < vigente_desde (nunca llegó a cubrir
                # un día completo) -- no tiene valor histórico, se borra en vez de
                # dejar un intervalo inválido.
                await self._session.delete(row)
            else:
                row.vigente_hasta = close_at
        # Flush explícito: si un mismo operador se reasigna el mismo día, la fila
        # vieja se borra y la nueva se inserta con el mismo (slot_id, user_id) --
        # sin este flush, el unit-of-work de SQLAlchemy puede emitir el INSERT
        # antes que el DELETE dentro del mismo flush y violar transitoriamente
        # el índice único parcial (vigente_hasta IS NULL).
        await self._session.flush()
        for a in asignaciones:
            model = TurnoAsignacionModel(
                id=a.id,
                slot_id=a.slot_id,
                user_id=a.user_id,
                vigente_desde=a.vigente_desde,
                vigente_hasta=a.vigente_hasta,
            )
            self._session.add(model)
        await self._session.flush()

    async def delete_by_slot(self, slot_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(TurnoAsignacionModel).where(TurnoAsignacionModel.slot_id == slot_id)
        )
        await self._session.flush()


def _to_asignacion_entity(model: TurnoAsignacionModel) -> Asignacion:
    return Asignacion(
        id=model.id,
        slot_id=model.slot_id,
        user_id=model.user_id,
        vigente_desde=model.vigente_desde,
        vigente_hasta=model.vigente_hasta,
    )
