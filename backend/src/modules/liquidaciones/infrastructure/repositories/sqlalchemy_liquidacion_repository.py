"""Implementación Postgres del puerto LiquidacionRepository (tabla liquidaciones)."""

import uuid
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion
from src.modules.liquidaciones.infrastructure.models.liquidacion_model import LiquidacionModel


class SqlAlchemyLiquidacionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, liquidacion_id: UUID) -> Liquidacion | None:
        row = await self._session.get(LiquidacionModel, liquidacion_id)
        return _to_entity(row) if row else None

    async def list_filtered(
        self,
        prestador_id: UUID | None = None,
        estado: str | None = None,
        periodo: str | None = None,
    ) -> list[Liquidacion]:
        stmt = select(LiquidacionModel).order_by(LiquidacionModel.fecha_importacion.desc())
        if prestador_id is not None:
            stmt = stmt.where(LiquidacionModel.prestador_id == prestador_id)
        if estado is not None:
            stmt = stmt.where(LiquidacionModel.estado == estado)
        if periodo is not None:
            stmt = stmt.where(LiquidacionModel.periodo == periodo)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def list_periodos(self) -> list[str]:
        stmt = (
            select(LiquidacionModel.periodo)
            .distinct()
            .order_by(LiquidacionModel.periodo.desc())
        )
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]

    async def list_by_prestador(self, prestador_id: UUID) -> list[Liquidacion]:
        return await self.list_filtered(prestador_id=prestador_id)

    async def list_all(self) -> list[Liquidacion]:
        return await self.list_filtered()

    async def create(
        self,
        *,
        prestador_id: UUID,
        numero_liquidacion: str | None,
        periodo: str,
        tipo_liquidacion: str,
        nombre_archivo: str | None,
        total_incidentes: int,
        total_importe: float,
    ) -> Liquidacion:
        model = LiquidacionModel(
            id=uuid.uuid4(),
            prestador_id=prestador_id,
            numero_liquidacion=numero_liquidacion,
            periodo=periodo,
            tipo_liquidacion=tipo_liquidacion,
            nombre_archivo=nombre_archivo,
            total_incidentes=total_incidentes,
            total_importe=total_importe,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update_estado(self, liquidacion_id: UUID, estado: str) -> Liquidacion | None:
        row = await self._session.get(LiquidacionModel, liquidacion_id)
        if row is None:
            return None
        stmt = (
            update(LiquidacionModel)
            .where(LiquidacionModel.id == liquidacion_id)
            .values(estado=estado)
        )
        await self._session.execute(stmt)
        await self._session.refresh(row)
        return _to_entity(row)

    async def update_extra(
        self,
        liquidacion_id: UUID,
        concepto_extra: str | None,
        monto_extra: float | None,
    ) -> Liquidacion | None:
        row = await self._session.get(LiquidacionModel, liquidacion_id)
        if row is None:
            return None
        stmt = (
            update(LiquidacionModel)
            .where(LiquidacionModel.id == liquidacion_id)
            .values(concepto_extra=concepto_extra, monto_extra=monto_extra)
        )
        await self._session.execute(stmt)
        await self._session.refresh(row)
        return _to_entity(row)

    async def update_total_alertas(self, liquidacion_id: UUID, total_alertas: int) -> None:
        stmt = (
            update(LiquidacionModel)
            .where(LiquidacionModel.id == liquidacion_id)
            .values(total_alertas=total_alertas)
        )
        await self._session.execute(stmt)

    async def delete(self, liquidacion_id: UUID) -> bool:
        row = await self._session.get(LiquidacionModel, liquidacion_id)
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True


def _to_entity(row: LiquidacionModel) -> Liquidacion:
    return Liquidacion(
        id=row.id,
        prestador_id=row.prestador_id,
        numero_liquidacion=row.numero_liquidacion,
        periodo=row.periodo,
        tipo_liquidacion=row.tipo_liquidacion,
        nombre_archivo=row.nombre_archivo,
        fecha_importacion=row.fecha_importacion,
        estado=row.estado,
        total_incidentes=row.total_incidentes,
        total_alertas=row.total_alertas,
        total_importe=row.total_importe,
        concepto_extra=row.concepto_extra,
        monto_extra=row.monto_extra,
    )
