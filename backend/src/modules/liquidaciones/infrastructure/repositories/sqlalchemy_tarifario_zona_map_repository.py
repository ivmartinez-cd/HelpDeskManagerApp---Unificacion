"""Implementación Postgres del puerto TarifarioZonaMapRepository."""

import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.tarifario_zona_map import TarifarioZonaMap
from src.modules.liquidaciones.infrastructure.models.tarifario_zona_map_model import (
    TarifarioZonaMapModel,
)


class SqlAlchemyTarifarioZonaMapRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[TarifarioZonaMap]:
        stmt = select(TarifarioZonaMapModel).order_by(
            TarifarioZonaMapModel.prestador_id, TarifarioZonaMapModel.descripcion_siges
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def upsert(
        self, *, prestador_id: UUID, descripcion_siges: str, zona_local: str | None
    ) -> TarifarioZonaMap:
        stmt = select(TarifarioZonaMapModel).where(
            TarifarioZonaMapModel.prestador_id == prestador_id,
            TarifarioZonaMapModel.descripcion_siges == descripcion_siges,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            row = TarifarioZonaMapModel(
                id=uuid.uuid4(),
                prestador_id=prestador_id,
                descripcion_siges=descripcion_siges,
                zona_local=zona_local,
            )
            self._session.add(row)
        else:
            row.zona_local = zona_local
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)


def _to_entity(row: TarifarioZonaMapModel) -> TarifarioZonaMap:
    return TarifarioZonaMap(
        id=row.id,
        prestador_id=row.prestador_id,
        descripcion_siges=row.descripcion_siges,
        zona_local=row.zona_local,
        created_at=row.created_at,
    )
