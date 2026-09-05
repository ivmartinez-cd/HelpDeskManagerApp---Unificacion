import uuid
from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.prestadores.domain.entities.asignacion_historial import AsignacionHistorial
from src.modules.prestadores.domain.services.historial_asignacion import (
    planificar_reasignacion,
)
from src.modules.prestadores.infrastructure.models.prestador_models import (
    PrestadorAsignacionHistorialModel,
)


class SqlAlchemyAsignacionHistorialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_prestador(self, prestador_id: uuid.UUID) -> list[AsignacionHistorial]:
        stmt = select(PrestadorAsignacionHistorialModel).where(
            PrestadorAsignacionHistorialModel.prestador_id == prestador_id
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_vigentes_a(self, fecha: date) -> dict[uuid.UUID, uuid.UUID | None]:
        stmt = select(
            PrestadorAsignacionHistorialModel.prestador_id,
            PrestadorAsignacionHistorialModel.operador_id,
        ).where(
            PrestadorAsignacionHistorialModel.desde <= fecha,
            or_(
                PrestadorAsignacionHistorialModel.hasta.is_(None),
                PrestadorAsignacionHistorialModel.hasta >= fecha,
            ),
        )
        rows = (await self._session.execute(stmt)).all()
        return {prestador_id: operador_id for prestador_id, operador_id in rows}

    async def reasignar(
        self, prestador_id: uuid.UUID, operador_id: uuid.UUID | None, desde: date
    ) -> None:
        stmt = select(PrestadorAsignacionHistorialModel).where(
            PrestadorAsignacionHistorialModel.prestador_id == prestador_id
        )
        tramos = list((await self._session.execute(stmt)).scalars().all())
        plan = planificar_reasignacion(tramos, desde)
        for row in plan.borrar:
            await self._session.delete(row)
        for row in plan.cerrar:
            row.hasta = plan.cierre

        self._session.add(
            PrestadorAsignacionHistorialModel(
                id=uuid.uuid4(),
                prestador_id=prestador_id,
                operador_id=operador_id,
                desde=desde,
                hasta=None,
            )
        )
        await self._session.flush()


def _to_entity(model: PrestadorAsignacionHistorialModel) -> AsignacionHistorial:
    return AsignacionHistorial(
        id=model.id,
        prestador_id=model.prestador_id,
        operador_id=model.operador_id,
        desde=model.desde,
        hasta=model.hasta,
    )
