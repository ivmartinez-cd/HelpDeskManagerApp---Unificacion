import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.prestadores.domain.entities.asignacion_historial import AsignacionHistorial
from src.modules.prestadores.infrastructure.models.prestador_models import (
    PrestadorAsignacionHistorialModel,
)

_ONE_DAY = timedelta(days=1)


class SqlAlchemyAsignacionHistorialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_prestador(self, prestador_id: uuid.UUID) -> list[AsignacionHistorial]:
        stmt = select(PrestadorAsignacionHistorialModel).where(
            PrestadorAsignacionHistorialModel.prestador_id == prestador_id
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def reasignar(
        self, prestador_id: uuid.UUID, operador_id: uuid.UUID | None, desde: date
    ) -> None:
        close_at = desde - _ONE_DAY
        stmt = select(PrestadorAsignacionHistorialModel).where(
            PrestadorAsignacionHistorialModel.prestador_id == prestador_id,
            PrestadorAsignacionHistorialModel.hasta.is_(None),
        )
        open_rows = (await self._session.execute(stmt)).scalars().all()
        for row in open_rows:
            if row.desde > close_at:
                # Cerrarlo dejaría hasta < desde (nunca llegó a cubrir un día
                # completo) -- sin valor histórico, se borra en vez de dejar
                # un intervalo inválido (mismo criterio que turnos).
                await self._session.delete(row)
            else:
                row.hasta = close_at

        model = PrestadorAsignacionHistorialModel(
            id=uuid.uuid4(),
            prestador_id=prestador_id,
            operador_id=operador_id,
            desde=desde,
            hasta=None,
        )
        self._session.add(model)
        await self._session.flush()


def _to_entity(model: PrestadorAsignacionHistorialModel) -> AsignacionHistorial:
    return AsignacionHistorial(
        id=model.id,
        prestador_id=model.prestador_id,
        operador_id=model.operador_id,
        desde=model.desde,
        hasta=model.hasta,
    )
