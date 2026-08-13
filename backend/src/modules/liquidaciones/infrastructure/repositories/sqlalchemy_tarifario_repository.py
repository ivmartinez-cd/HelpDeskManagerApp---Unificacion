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

    async def get_by_id(self, tarifario_id: UUID) -> Tarifario | None:
        row = await self._session.get(TarifarioModel, tarifario_id)
        return _to_entity(row) if row else None

    async def list_by_prestador(self, prestador_id: UUID) -> list[Tarifario]:
        stmt = select(TarifarioModel).where(TarifarioModel.prestador_id == prestador_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def list_all(self) -> list[Tarifario]:
        stmt = select(TarifarioModel)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def list_grupo(
        self, *, prestador_id: UUID, tipo_servicio: str, zona: str | None
    ) -> list[Tarifario]:
        stmt = select(TarifarioModel).where(
            TarifarioModel.prestador_id == prestador_id,
            TarifarioModel.tipo_servicio == tipo_servicio,
            TarifarioModel.zona.is_(None) if zona is None else TarifarioModel.zona == zona,
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def set_vigencia_hasta(self, tarifario_id: UUID, vigencia_hasta: date | None) -> None:
        row = await self._session.get(TarifarioModel, tarifario_id)
        if row is None:
            return
        row.vigencia_hasta = vigencia_hasta
        await self._session.flush()

    async def update(
        self,
        tarifario_id: UUID,
        *,
        prestador_id: UUID,
        tipo_servicio: str,
        zona: str | None,
        costo_servicio: float,
        costo_km: float,
        vigencia_desde: date,
        vigencia_hasta: date | None,
    ) -> Tarifario | None:
        row = await self._session.get(TarifarioModel, tarifario_id)
        if row is None:
            return None
        row.prestador_id = prestador_id
        row.tipo_servicio = tipo_servicio
        row.zona = zona
        row.costo_servicio = costo_servicio
        row.costo_km = costo_km
        row.vigencia_desde = vigencia_desde
        row.vigencia_hasta = vigencia_hasta
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def delete(self, tarifario_id: UUID) -> bool:
        row = await self._session.get(TarifarioModel, tarifario_id)
        if not row:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True

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
