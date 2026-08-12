"""Implementación Postgres del puerto TarifarioRepository (tabla tarifarios)."""

import uuid
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.infrastructure.models.tarifario_model import TarifarioModel


class SqlAlchemyTarifarioRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_prestador(self, prestador_id: UUID) -> list[Tarifario]:
        stmt = select(TarifarioModel).where(TarifarioModel.prestador_id == prestador_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def create(
        self,
        *,
        prestador_id: UUID,
        tipo_servicio: str,
        zona: str | None,
        costo_servicio: float,
        costo_km: float,
        vigencia_desde: date,
        vigencia_hasta: date | None,
    ) -> Tarifario:
        model = TarifarioModel(
            id=uuid.uuid4(),
            prestador_id=prestador_id,
            tipo_servicio=tipo_servicio,
            zona=zona,
            costo_servicio=costo_servicio,
            costo_km=costo_km,
            vigencia_desde=vigencia_desde,
            vigencia_hasta=vigencia_hasta,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)


def _to_entity(row: TarifarioModel) -> Tarifario:
    return Tarifario(
        id=row.id,
        prestador_id=row.prestador_id,
        tipo_servicio=row.tipo_servicio,
        zona=row.zona,
        costo_servicio=row.costo_servicio,
        costo_km=row.costo_km,
        vigencia_desde=row.vigencia_desde,
        vigencia_hasta=row.vigencia_hasta,
        created_at=row.created_at,
    )
