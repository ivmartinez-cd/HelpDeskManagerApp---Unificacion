"""Implementación Postgres del puerto ResolucionRepository (tabla resoluciones)."""

import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.resolucion import Resolucion
from src.modules.liquidaciones.infrastructure.models.resolucion_model import ResolucionModel


class SqlAlchemyResolucionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_alerta(self, alerta_id: UUID) -> list[Resolucion]:
        stmt = select(ResolucionModel).where(ResolucionModel.alerta_id == alerta_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def create(
        self, *, alerta_id: UUID, decision: str, justificacion: str | None, comentario: str | None
    ) -> Resolucion:
        model = ResolucionModel(
            id=uuid.uuid4(),
            alerta_id=alerta_id,
            decision=decision,
            justificacion=justificacion,
            comentario=comentario,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)


def _to_entity(row: ResolucionModel) -> Resolucion:
    return Resolucion(
        id=row.id,
        alerta_id=row.alerta_id,
        decision=row.decision,
        justificacion=row.justificacion,
        comentario=row.comentario,
        fecha=row.fecha,
    )
