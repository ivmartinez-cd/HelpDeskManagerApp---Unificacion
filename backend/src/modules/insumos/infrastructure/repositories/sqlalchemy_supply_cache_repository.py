"""Implementación Postgres del puerto SupplyCacheRepository.

Replica la semántica del upsert del legacy (db/supplies.py): ante conflicto por
supply_id, serial/estado/fecha se pisan siempre; empresa_id/sku/description solo si el
valor nuevo no es vacío (el scan trae menos datos que la creación y no debe borrarlos).
"""

from collections.abc import Sequence

from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply
from src.modules.insumos.infrastructure.models.supply_serial_cache_model import (
    SupplySerialCacheModel,
)


class SqlAlchemySupplyCacheRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, entries: Sequence[CachedSupply]) -> None:
        if not entries:
            return
        stmt = pg_insert(SupplySerialCacheModel).values(
            [
                {
                    "supply_id": e.supply_id,
                    "serial": e.serial,
                    "estado": e.estado,
                    "empresa_id": e.empresa_id,
                    "fecha": e.fecha,
                    "sku": e.sku,
                    "description": e.description,
                }
                for e in entries
            ]
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["supply_id"],
            set_={
                "serial": stmt.excluded.serial,
                "estado": stmt.excluded.estado,
                "fecha": stmt.excluded.fecha,
                "empresa_id": func.coalesce(
                    func.nullif(stmt.excluded.empresa_id, ""), SupplySerialCacheModel.empresa_id
                ),
                "sku": case(
                    (stmt.excluded.sku != "", stmt.excluded.sku),
                    else_=SupplySerialCacheModel.sku,
                ),
                "description": case(
                    (stmt.excluded.description != "", stmt.excluded.description),
                    else_=SupplySerialCacheModel.description,
                ),
                "cached_at": func.now(),
            },
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_by_serial(self, serial: str, limit: int = 20) -> list[CachedSupply]:
        stmt = (
            select(SupplySerialCacheModel)
            .where(func.lower(SupplySerialCacheModel.serial) == serial.lower())
            .order_by(SupplySerialCacheModel.supply_id.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            CachedSupply(
                supply_id=row.supply_id,
                serial=row.serial,
                estado=row.estado or "",
                empresa_id=row.empresa_id or "",
                fecha=row.fecha,
                sku=row.sku or "",
                description=row.description or "",
            )
            for row in rows
        ]
