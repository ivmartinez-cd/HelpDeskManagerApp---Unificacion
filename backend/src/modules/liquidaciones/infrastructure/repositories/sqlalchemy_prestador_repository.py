"""Implementación Postgres del puerto PrestadorRepository (tabla prestadores)."""

import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.infrastructure.models.prestador_model import (
    LiquidacionPrestadorModel,
)


class SqlAlchemyPrestadorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, prestador_id: UUID) -> Prestador | None:
        row = await self._session.get(LiquidacionPrestadorModel, prestador_id)
        return _to_entity(row) if row else None

    async def get_by_nombre_corto(self, nombre_corto: str) -> Prestador | None:
        stmt = select(LiquidacionPrestadorModel).where(
            LiquidacionPrestadorModel.nombre_corto == nombre_corto
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def list_all(self, *, solo_activos: bool = False) -> list[Prestador]:
        stmt = select(LiquidacionPrestadorModel).order_by(LiquidacionPrestadorModel.nombre)
        if solo_activos:
            stmt = stmt.where(LiquidacionPrestadorModel.activo.is_(True))
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def create(
        self, *, nombre: str, nombre_corto: str, cuit: str | None, region: str | None
    ) -> Prestador:
        model = LiquidacionPrestadorModel(
            id=uuid.uuid4(),
            nombre=nombre,
            nombre_corto=nombre_corto,
            cuit=cuit,
            region=region,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(
        self,
        prestador_id: UUID,
        *,
        nombre: str,
        nombre_corto: str,
        cuit: str | None,
        region: str | None,
    ) -> Prestador | None:
        row = await self._session.get(LiquidacionPrestadorModel, prestador_id)
        if not row:
            return None
        row.nombre = nombre
        row.nombre_corto = nombre_corto
        row.cuit = cuit
        row.region = region
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def toggle_activo(self, prestador_id: UUID, *, activo: bool) -> Prestador | None:
        row = await self._session.get(LiquidacionPrestadorModel, prestador_id)
        if not row:
            return None
        row.activo = activo
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)


def _to_entity(row: LiquidacionPrestadorModel) -> Prestador:
    return Prestador(
        id=row.id,
        nombre=row.nombre,
        nombre_corto=row.nombre_corto,
        cuit=row.cuit,
        region=row.region,
        activo=row.activo,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
