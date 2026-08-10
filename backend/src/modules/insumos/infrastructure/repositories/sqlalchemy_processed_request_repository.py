"""Implementación Postgres del puerto ProcessedRequestRepository."""

from collections.abc import Sequence

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.processed_request import (
    STATUS_CANCELLED,
    STATUS_CREATED,
    ProcessedRequest,
)
from src.modules.insumos.infrastructure.models.processed_request_model import (
    ProcessedRequestModel,
)
from src.modules.insumos.infrastructure.repositories._argentina_day import is_today_argentina


class SqlAlchemyProcessedRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, hp_request_id: int) -> ProcessedRequest | None:
        row = await self._session.get(ProcessedRequestModel, hp_request_id)
        return _to_entity(row) if row else None

    async def mark_processed(self, request: ProcessedRequest) -> None:
        values = {
            "hp_request_id": request.hp_request_id,
            "device_id": request.device_id,
            "device_serial": request.device_serial,
            "customer_id": request.customer_id,
            "sku": request.sku,
            "internal_order_id": request.internal_order_id,
            "status": request.status,
            "description": request.description,
            "initial_percent_left": request.initial_percent_left,
            "initial_days_left": request.initial_days_left,
            "initial_pages_left": request.initial_pages_left,
        }
        stmt = pg_insert(ProcessedRequestModel).values(**values)
        # Reprocesar pisa el registro entero y renueva created_at (mismo criterio que
        # el ON CONFLICT del legacy: created_at = excluded.created_at).
        stmt = stmt.on_conflict_do_update(
            index_elements=["hp_request_id"],
            set_={**values, "created_at": func.now(), "updated_at": func.now()},
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def mark_cancelled(self, hp_request_id: int) -> None:
        stmt = (
            update(ProcessedRequestModel)
            .where(ProcessedRequestModel.hp_request_id == hp_request_id)
            .values(status=STATUS_CANCELLED, updated_at=func.now())
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_today_order_for(self, device_serial: str, sku: str) -> ProcessedRequest | None:
        stmt = (
            select(ProcessedRequestModel)
            .where(
                ProcessedRequestModel.device_serial == device_serial,
                ProcessedRequestModel.sku == sku,
                ProcessedRequestModel.status == STATUS_CREATED,
                is_today_argentina(ProcessedRequestModel.created_at),
            )
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def get_created_by_serial(self, device_serial: str) -> list[ProcessedRequest]:
        stmt = (
            select(ProcessedRequestModel)
            .where(
                func.lower(ProcessedRequestModel.device_serial) == device_serial.lower(),
                ProcessedRequestModel.status == STATUS_CREATED,
            )
            .order_by(ProcessedRequestModel.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def get_processed_ids(self, hp_request_ids: Sequence[int]) -> set[int]:
        if not hp_request_ids:
            return set()
        stmt = select(ProcessedRequestModel.hp_request_id).where(
            ProcessedRequestModel.hp_request_id.in_(hp_request_ids),
            ProcessedRequestModel.status == STATUS_CREATED,
        )
        return set((await self._session.execute(stmt)).scalars().all())

    async def get_supply_ids(self, hp_request_ids: Sequence[int]) -> dict[int, int]:
        if not hp_request_ids:
            return {}
        stmt = select(
            ProcessedRequestModel.hp_request_id, ProcessedRequestModel.internal_order_id
        ).where(
            ProcessedRequestModel.hp_request_id.in_(hp_request_ids),
            ProcessedRequestModel.status == STATUS_CREATED,
            ProcessedRequestModel.internal_order_id.not_like("DRYRUN%"),
        )
        rows = (await self._session.execute(stmt)).all()
        result: dict[int, int] = {}
        for hp_request_id, internal_order_id in rows:
            try:
                result[hp_request_id] = int(str(internal_order_id).split("-")[0])
            except (ValueError, IndexError):
                continue
        return result

    async def get_today_processed_ids(self, hp_request_ids: Sequence[int]) -> set[int]:
        if not hp_request_ids:
            return set()
        stmt = select(ProcessedRequestModel.hp_request_id).where(
            ProcessedRequestModel.hp_request_id.in_(hp_request_ids),
            ProcessedRequestModel.status == STATUS_CREATED,
            is_today_argentina(ProcessedRequestModel.created_at),
        )
        return set((await self._session.execute(stmt)).scalars().all())

    async def count_processed_today(self) -> int:
        stmt = select(func.count()).where(
            ProcessedRequestModel.status == STATUS_CREATED,
            is_today_argentina(ProcessedRequestModel.created_at),
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def get_created_by_serials(
        self, device_serials: Sequence[str]
    ) -> dict[str, list[ProcessedRequest]]:
        if not device_serials:
            return {}
        stmt = (
            select(ProcessedRequestModel)
            .where(
                func.upper(ProcessedRequestModel.device_serial).in_(
                    [s.upper() for s in device_serials]
                ),
                ProcessedRequestModel.status == STATUS_CREATED,
            )
            .order_by(ProcessedRequestModel.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        result: dict[str, list[ProcessedRequest]] = {}
        for row in rows:
            result.setdefault((row.device_serial or "").upper(), []).append(_to_entity(row))
        return result


def _to_entity(row: ProcessedRequestModel) -> ProcessedRequest:
    return ProcessedRequest(
        hp_request_id=row.hp_request_id,
        status=row.status,
        device_id=row.device_id,
        device_serial=row.device_serial or "",
        customer_id=row.customer_id,
        sku=row.sku or "",
        internal_order_id=row.internal_order_id or "",
        description=row.description or "",
        initial_percent_left=row.initial_percent_left,
        initial_days_left=row.initial_days_left,
        initial_pages_left=row.initial_pages_left,
        created_at=row.created_at,
    )
