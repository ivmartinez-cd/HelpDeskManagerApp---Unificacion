"""Implementación Postgres del puerto MatchingDescarteRepository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.infrastructure.models.matching_descarte_model import (
    MatchingDescarteModel,
)


class SqlAlchemyMatchingDescarteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, tabla_km_id: UUID, siges_sucursal_id: int, usuario_email: str
    ) -> None:
        stmt = (
            pg_insert(MatchingDescarteModel)
            .values(
                tabla_km_id=tabla_km_id,
                siges_sucursal_id=siges_sucursal_id,
                usuario_email=usuario_email,
            )
            .on_conflict_do_nothing(
                index_elements=["tabla_km_id", "siges_sucursal_id"]
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def list_descartados_por_fila(
        self, tabla_km_ids: list[UUID]
    ) -> dict[UUID, set[int]]:
        if not tabla_km_ids:
            return {}
        stmt = select(
            MatchingDescarteModel.tabla_km_id, MatchingDescarteModel.siges_sucursal_id
        ).where(MatchingDescarteModel.tabla_km_id.in_(tabla_km_ids))
        rows = (await self._session.execute(stmt)).all()
        resultado: dict[UUID, set[int]] = {}
        for tabla_km_id, siges_sucursal_id in rows:
            resultado.setdefault(tabla_km_id, set()).add(siges_sucursal_id)
        return resultado
