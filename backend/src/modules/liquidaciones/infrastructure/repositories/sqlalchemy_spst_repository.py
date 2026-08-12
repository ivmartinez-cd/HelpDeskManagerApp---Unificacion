"""Implementación Postgres del puerto SpstRepository (tabla spsts)."""

import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.infrastructure.models.spst_model import SpstModel


class SqlAlchemySpstRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, spst_id: UUID) -> Spst | None:
        row = await self._session.get(SpstModel, spst_id)
        return _to_entity(row) if row else None

    async def list_by_prestador(self, prestador_id: UUID) -> list[Spst]:
        stmt = select(SpstModel).where(SpstModel.prestador_id == prestador_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def create(
        self,
        *,
        prestador_id: UUID,
        nombre: str,
        domicilio: str | None,
        localidad: str | None,
        provincia: str | None,
        zona: str | None,
    ) -> Spst:
        model = SpstModel(
            id=uuid.uuid4(),
            prestador_id=prestador_id,
            nombre=nombre,
            domicilio=domicilio,
            localidad=localidad,
            provincia=provincia,
            zona=zona,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)


def _to_entity(row: SpstModel) -> Spst:
    return Spst(
        id=row.id,
        prestador_id=row.prestador_id,
        nombre=row.nombre,
        domicilio=row.domicilio,
        localidad=row.localidad,
        provincia=row.provincia,
        zona=row.zona,
        activo=row.activo,
        created_at=row.created_at,
    )
