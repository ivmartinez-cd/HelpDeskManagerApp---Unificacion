"""Implementación Postgres del puerto ModificacionPrestadorRepository
(modificaciones_prestador)."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.modificacion_prestador import (
    ModificacionPrestador,
)
from src.modules.liquidaciones.infrastructure.models.modificacion_prestador_model import (
    ModificacionPrestadorModel,
)


class SqlAlchemyModificacionPrestadorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_create(self, modificaciones: Sequence[ModificacionPrestador]) -> None:
        if not modificaciones:
            return
        self._session.add_all(_a_model(m) for m in modificaciones)
        await self._session.flush()

    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[ModificacionPrestador]:
        stmt = (
            select(ModificacionPrestadorModel)
            .where(ModificacionPrestadorModel.liquidacion_id == liquidacion_id)
            .order_by(ModificacionPrestadorModel.detectada_en.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_no_vistas(self) -> list[ModificacionPrestador]:
        stmt = (
            select(ModificacionPrestadorModel)
            .where(ModificacionPrestadorModel.vista_en.is_(None))
            .order_by(ModificacionPrestadorModel.detectada_en.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def marcar_vistas(self, liquidacion_id: UUID) -> int:
        from sqlalchemy.engine import CursorResult

        stmt = (
            update(ModificacionPrestadorModel)
            .where(
                ModificacionPrestadorModel.liquidacion_id == liquidacion_id,
                ModificacionPrestadorModel.vista_en.is_(None),
            )
            .values(vista_en=func.now())
        )
        resultado: CursorResult[tuple[()]] = await self._session.execute(  # type: ignore[assignment]
            stmt
        )
        await self._session.flush()
        return int(resultado.rowcount)


def _a_model(entidad: ModificacionPrestador) -> ModificacionPrestadorModel:
    return ModificacionPrestadorModel(
        id=entidad.id,
        liquidacion_id=entidad.liquidacion_id,
        numero_incidente=entidad.numero_incidente,
        tipo_cambio=entidad.tipo_cambio,
        campo=entidad.campo,
        valor_anterior=entidad.valor_anterior,
        valor_nuevo=entidad.valor_nuevo,
        detectada_en=entidad.detectada_en,
        vista_en=entidad.vista_en,
    )


def _to_entity(row: ModificacionPrestadorModel) -> ModificacionPrestador:
    return ModificacionPrestador(
        id=row.id,
        liquidacion_id=row.liquidacion_id,
        numero_incidente=row.numero_incidente,
        tipo_cambio=row.tipo_cambio,
        campo=row.campo,
        valor_anterior=row.valor_anterior,
        valor_nuevo=row.valor_nuevo,
        detectada_en=row.detectada_en,
        vista_en=row.vista_en,
    )
