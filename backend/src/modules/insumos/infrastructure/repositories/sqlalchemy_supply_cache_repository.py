"""Implementación Postgres del puerto SupplyCacheRepository.

Replica la semántica del upsert del legacy (db/supplies.py): ante conflicto por
supply_id, serial/estado/fecha se pisan siempre; empresa_id/sku/description solo si el
valor nuevo no es vacío (el scan trae menos datos que la creación y no debe borrarlos).
"""

from collections.abc import Sequence

from sqlalchemy import case, func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects import cd_state
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, SupplyStatusEvent
from src.modules.insumos.infrastructure.models.supply_serial_cache_model import (
    SupplySerialCacheModel,
)
from src.modules.insumos.infrastructure.models.supply_status_history_model import (
    SupplyStatusHistoryModel,
)

# Mismo conjunto que el WHERE del legacy (find_active_supply_by_serial): un pedido
# Entregado tampoco es "activo" a los fines del bloqueo anti-duplicado.
_TERMINAL_STATES = tuple(cd_state.INACTIVE_STATES)


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
        await self._record_status_history(entries)
        await self._session.flush()

    async def _record_status_history(self, entries: Sequence[CachedSupply]) -> None:
        """Primer avistaje de cada estado distinto — dedup por (supply_id, estado):
        re-escanear el mismo supply mil veces no agrega filas. Sin whitelist: un
        estado real desconocido no debe perderse en silencio (ver cd_state.py)."""
        # Dedup previo en memoria: un INSERT con la misma (supply_id, estado) dos veces
        # rompería el ON CONFLICT dentro del mismo statement.
        unique = {(e.supply_id, e.estado) for e in entries if e.estado.strip()}
        if not unique:
            return
        history = [{"supply_id": sid, "estado": estado} for sid, estado in sorted(unique)]
        stmt = pg_insert(SupplyStatusHistoryModel).values(history)
        await self._session.execute(
            stmt.on_conflict_do_nothing(index_elements=["supply_id", "estado"])
        )

    async def get_status_history_batch(
        self, supply_ids: Sequence[int]
    ) -> dict[int, list[SupplyStatusEvent]]:
        if not supply_ids:
            return {}
        stmt = (
            select(SupplyStatusHistoryModel)
            .where(SupplyStatusHistoryModel.supply_id.in_(supply_ids))
            .order_by(
                SupplyStatusHistoryModel.supply_id,
                SupplyStatusHistoryModel.first_seen_at.asc(),
                SupplyStatusHistoryModel.id.asc(),
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        result: dict[int, list[SupplyStatusEvent]] = {}
        for row in rows:
            result.setdefault(row.supply_id, []).append(
                SupplyStatusEvent(estado=row.estado, first_seen_at=row.first_seen_at)
            )
        return result

    async def get_by_serial(self, serial: str, limit: int = 20) -> list[CachedSupply]:
        stmt = (
            select(SupplySerialCacheModel)
            .where(func.lower(SupplySerialCacheModel.serial) == serial.lower())
            .order_by(SupplySerialCacheModel.supply_id.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def find_active_by_serial(self, serial: str) -> CachedSupply | None:
        stmt = (
            select(SupplySerialCacheModel)
            .where(
                func.lower(SupplySerialCacheModel.serial) == serial.lower(),
                SupplySerialCacheModel.estado.notin_(_TERMINAL_STATES),
            )
            .order_by(SupplySerialCacheModel.supply_id.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def get_status(self, supply_id: int) -> str | None:
        row = await self._session.get(SupplySerialCacheModel, supply_id)
        return row.estado if row else None

    async def get_statuses_batch(self, supply_ids: Sequence[int]) -> dict[int, str]:
        if not supply_ids:
            return {}
        stmt = select(SupplySerialCacheModel.supply_id, SupplySerialCacheModel.estado).where(
            SupplySerialCacheModel.supply_id.in_(supply_ids),
            SupplySerialCacheModel.estado.is_not(None),
        )
        rows = (await self._session.execute(stmt)).all()
        return {supply_id: estado for supply_id, estado in rows}

    async def get_recently_cached_ids(
        self, supply_ids: Sequence[int], within_seconds: int
    ) -> set[int]:
        if not supply_ids:
            return set()
        cutoff = func.now() - text(f"interval '{int(within_seconds)} seconds'")
        stmt = select(SupplySerialCacheModel.supply_id).where(
            SupplySerialCacheModel.supply_id.in_(supply_ids),
            SupplySerialCacheModel.cached_at >= cutoff,
        )
        return set((await self._session.execute(stmt)).scalars().all())

    async def get_noncancelled_by_serials(
        self, serials: Sequence[str]
    ) -> dict[str, list[CachedSupply]]:
        if not serials:
            return {}
        stmt = (
            select(SupplySerialCacheModel)
            .where(
                func.upper(SupplySerialCacheModel.serial).in_([s.upper() for s in serials]),
                SupplySerialCacheModel.estado.notin_((cd_state.ANULADO, cd_state.CANCELADO)),
            )
            .order_by(SupplySerialCacheModel.supply_id.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        result: dict[str, list[CachedSupply]] = {}
        for row in rows:
            result.setdefault(row.serial.upper(), []).append(_to_entity(row))
        return result


def _to_entity(row: SupplySerialCacheModel) -> CachedSupply:
    return CachedSupply(
        supply_id=row.supply_id,
        serial=row.serial,
        estado=row.estado or "",
        empresa_id=row.empresa_id or "",
        fecha=row.fecha,
        sku=row.sku or "",
        description=row.description or "",
    )
