"""Implementación Postgres del puerto OrderAuditRepository."""

from collections.abc import Sequence

from sqlalchemy import ColumnElement, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CANCELLED,
    EVENT_CREATED,
    EVENT_RELEASED,
    AuditRecord,
    AuditSnapshot,
    StoredAuditRecord,
)
from src.modules.insumos.domain.value_objects.audit_history import AuditClosures, AuditFilters
from src.modules.insumos.infrastructure.models.order_audit_model import OrderAuditModel
from src.modules.insumos.infrastructure.repositories._argentina_day import (
    argentina_day,
    is_today_argentina,
)

_CLOSURE_EVENTS = (EVENT_CREATED, EVENT_CANCELLED, EVENT_RELEASED)

_SEARCH_COLUMNS = (
    OrderAuditModel.customer_name,
    OrderAuditModel.device_serial,
    OrderAuditModel.sku,
    OrderAuditModel.description,
    OrderAuditModel.internal_order_id,
    OrderAuditModel.detail,
)


def _escape_like(term: str) -> str:
    """El `includes()` que hoy hace el frontend es literal, sin comodines — sin
    este escape un `%`/`_` tipeado por el usuario actuaría como wildcard de LIKE."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _conditions(f: AuditFilters) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if f.events is not None:
        conditions.append(OrderAuditModel.event.in_(f.events))  # in_([]) → 0 filas
    day = argentina_day(OrderAuditModel.created_at)
    if f.start_day:
        conditions.append(day >= f.start_day)
    if f.end_day:
        conditions.append(day <= f.end_day)
    if f.search:
        like = f"%{_escape_like(f.search)}%"
        conditions.append(or_(*(c.ilike(like, escape="\\") for c in _SEARCH_COLUMNS)))
    return conditions


class SqlAlchemyOrderAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, entry: AuditRecord) -> None:
        self._session.add(
            OrderAuditModel(
                event=entry.event,
                hp_request_id=entry.hp_request_id,
                customer_id=entry.customer_id,
                customer_name=entry.customer_name,
                device_serial=entry.device_serial,
                sku=entry.sku,
                internal_order_id=entry.internal_order_id,
                detail=entry.detail,
                dry_run=entry.dry_run,
                hp_request_time=entry.hp_request_time,
                description=entry.description,
                device_id=entry.device_id,
                order_type=entry.order_type,
                initial_percent_left=entry.initial_percent_left,
                initial_days_left=entry.initial_days_left,
                initial_pages_left=entry.initial_pages_left,
            )
        )
        await self._session.flush()

    async def count_created_today(self, hp_request_id: int) -> int:
        stmt = select(func.count()).where(
            OrderAuditModel.event == EVENT_CREATED,
            OrderAuditModel.hp_request_id == hp_request_id,
            OrderAuditModel.dry_run.is_(False),
            is_today_argentina(OrderAuditModel.created_at),
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def list_page(
        self, filters: AuditFilters, limit: int, offset: int
    ) -> list[StoredAuditRecord]:
        stmt = (
            select(OrderAuditModel)
            .where(*_conditions(filters))
            .order_by(OrderAuditModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_stored(row) for row in rows]

    async def count(self, filters: AuditFilters) -> int:
        stmt = select(func.count()).select_from(OrderAuditModel).where(*_conditions(filters))
        return (await self._session.execute(stmt)).scalar_one()

    async def count_by_event(self, filters: AuditFilters) -> dict[str, int]:
        stmt = (
            select(OrderAuditModel.event, func.count())
            .where(*_conditions(filters))
            .group_by(OrderAuditModel.event)
        )
        rows = (await self._session.execute(stmt)).all()
        return {event: count for event, count in rows}

    async def closures_for(self, hp_request_ids: Sequence[int]) -> AuditClosures:
        if not hp_request_ids:
            return AuditClosures(last_created={}, last_closed={})
        stmt = (
            select(
                OrderAuditModel.hp_request_id,
                OrderAuditModel.event,
                func.max(OrderAuditModel.id),
            )
            .where(
                OrderAuditModel.hp_request_id.in_(hp_request_ids),
                OrderAuditModel.event.in_(_CLOSURE_EVENTS),
            )
            .group_by(OrderAuditModel.hp_request_id, OrderAuditModel.event)
        )
        rows = (await self._session.execute(stmt)).all()
        last_created: dict[int, int] = {}
        last_closed: dict[int, int] = {}
        for hp_request_id, event, max_id in rows:
            if event == EVENT_CREATED:
                last_created[hp_request_id] = max_id
            else:
                last_closed[hp_request_id] = max(last_closed.get(hp_request_id, 0), max_id)
        return AuditClosures(last_created=last_created, last_closed=last_closed)

    async def backfill_snapshots(self, updates: Sequence[AuditSnapshot]) -> None:
        for entry in updates:
            await self._session.execute(
                update(OrderAuditModel)
                .where(OrderAuditModel.id == entry.audit_id)
                .values(
                    device_id=entry.device_id,
                    initial_percent_left=entry.initial_percent_left,
                    initial_days_left=entry.initial_days_left,
                    initial_pages_left=entry.initial_pages_left,
                )
            )


def _to_stored(row: OrderAuditModel) -> StoredAuditRecord:
    return StoredAuditRecord(
        audit_id=row.id,
        created_at=row.created_at,
        event=row.event,
        hp_request_id=row.hp_request_id,
        customer_id=row.customer_id,
        customer_name=row.customer_name,
        device_serial=row.device_serial,
        sku=row.sku,
        internal_order_id=row.internal_order_id,
        detail=row.detail,
        dry_run=row.dry_run,
        hp_request_time=row.hp_request_time,
        description=row.description,
        device_id=row.device_id,
        order_type=row.order_type,
        initial_percent_left=row.initial_percent_left,
        initial_days_left=row.initial_days_left,
        initial_pages_left=row.initial_pages_left,
    )
