import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.domain.entities.aprobacion import Aprobacion, Decision
from src.modules.vacaciones.infrastructure.models.aprobacion_model import (
    VacacionesAprobacionModel,
)


def _to_entity(row: VacacionesAprobacionModel) -> Aprobacion:
    return Aprobacion(
        id=row.id,
        solicitud_id=row.solicitud_id,
        approver_user_id=row.approver_user_id,
        decision=Decision(row.decision),
        comment=row.comment,
        created_at=row.created_at,
    )


class SqlAlchemyAprobacionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, aprobacion: Aprobacion) -> None:
        self._session.add(
            VacacionesAprobacionModel(
                id=aprobacion.id,
                solicitud_id=aprobacion.solicitud_id,
                approver_user_id=aprobacion.approver_user_id,
                decision=aprobacion.decision.value,
                comment=aprobacion.comment,
            )
        )
        await self._session.flush()

    async def list_por_solicitudes(
        self, solicitud_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[Aprobacion]]:
        if not solicitud_ids:
            return {}
        stmt = (
            select(VacacionesAprobacionModel)
            .where(VacacionesAprobacionModel.solicitud_id.in_(solicitud_ids))
            .order_by(VacacionesAprobacionModel.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        grouped: dict[uuid.UUID, list[Aprobacion]] = {}
        for r in rows:
            grouped.setdefault(r.solicitud_id, []).append(_to_entity(r))
        return grouped

    async def list_por_solicitud(self, solicitud_id: uuid.UUID) -> list[Aprobacion]:
        stmt = (
            select(VacacionesAprobacionModel)
            .where(VacacionesAprobacionModel.solicitud_id == solicitud_id)
            .order_by(VacacionesAprobacionModel.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]
