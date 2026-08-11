"""Implementación Postgres del puerto AuditStatisticsRepository.

Toda la agregación vive en SQL (GROUP BY / SUM / COUNT) — nunca se traen las filas
crudas para contarlas en Python. Las dos únicas excepciones son fulfillment_rows y
dispatch_rows, que devuelven filas porque su cálculo depende de horario laboral y de
supply_status_history, no de una agregación expresable en la misma query.
"""

from datetime import date

from sqlalchemy import ColumnElement, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CREATED,
    EVENT_FAILED,
    ORDER_TYPE_SUPPLY,
)
from src.modules.insumos.domain.value_objects.audit_statistics import (
    CustomerActivity,
    DailyEventCount,
    DeviceCount,
    DispatchRow,
    FailureReasonCount,
    FulfillmentRow,
    RecentFailure,
    SkuCount,
    SourceSplit,
)
from src.modules.insumos.infrastructure.models.order_audit_model import OrderAuditModel
from src.modules.insumos.infrastructure.repositories._argentina_day import argentina_day

_AUDITED_EVENTS = (EVENT_CREATED, EVENT_FAILED)
_NO_DETAIL = "Sin detalle"
# El detalle de auto-carga tiene variantes ("Pre-Correctivo (kit de mantenimiento) —
# Auto-carga"), por eso se busca la subcadena y no el valor exacto.
_AUTOLOAD_MARK = "%Auto-carga%"
_DRYRUN_PREFIX = "DRYRUN%"


def _day() -> ColumnElement[date]:
    return argentina_day(OrderAuditModel.created_at)


def _in_range(
    start: date, end: date, customer_id: int | None = None
) -> list[ColumnElement[bool]]:
    filters = [OrderAuditModel.dry_run.is_(False), _day() >= start, _day() <= end]
    if customer_id is not None:
        filters.append(OrderAuditModel.customer_id == customer_id)
    return filters


def _count_of(event: str) -> ColumnElement[int]:
    return func.sum(case((OrderAuditModel.event == event, 1), else_=0))


class SqlAlchemyAuditStatisticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def earliest_day(self) -> date | None:
        stmt = select(func.min(_day())).where(OrderAuditModel.dry_run.is_(False))
        return (await self._session.execute(stmt)).scalars().first()

    async def customer_name(self, customer_id: int) -> str | None:
        stmt = (
            select(OrderAuditModel.customer_name)
            .where(
                OrderAuditModel.customer_id == customer_id,
                OrderAuditModel.customer_name.is_not(None),
                OrderAuditModel.customer_name != "",
            )
            .order_by(OrderAuditModel.id.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalars().first()

    async def daily_counts(
        self, start: date, end: date, *, customer_id: int | None = None
    ) -> list[DailyEventCount]:
        day = _day()
        stmt = (
            select(day, OrderAuditModel.event, func.count())
            .where(
                *_in_range(start, end, customer_id),
                OrderAuditModel.event.in_(_AUDITED_EVENTS),
            )
            .group_by(day, OrderAuditModel.event)
            .order_by(day)
        )
        rows = (await self._session.execute(stmt)).all()
        return [DailyEventCount(day=d, event=e, count=n) for d, e, n in rows]

    async def event_totals(
        self, start: date, end: date, *, customer_id: int | None = None
    ) -> dict[str, int]:
        stmt = (
            select(OrderAuditModel.event, func.count())
            .where(
                *_in_range(start, end, customer_id),
                OrderAuditModel.event.in_(_AUDITED_EVENTS),
            )
            .group_by(OrderAuditModel.event)
        )
        rows = (await self._session.execute(stmt)).all()
        return {event: total for event, total in rows}

    async def customer_activity(self, start: date, end: date) -> list[CustomerActivity]:
        stmt = (
            select(
                OrderAuditModel.customer_id,
                func.max(OrderAuditModel.customer_name),
                _count_of(EVENT_CREATED),
                _count_of(EVENT_FAILED),
                func.count(),
            )
            .where(
                *_in_range(start, end),
                OrderAuditModel.event.in_(_AUDITED_EVENTS),
                # Sin cliente no hay a quién rankear (eventos del sistema).
                OrderAuditModel.customer_id.is_not(None),
            )
            .group_by(OrderAuditModel.customer_id)
            .order_by(func.count().desc())
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            CustomerActivity(
                customer_id=cid, customer_name=name, created=c, failed=f, total=t
            )
            for cid, name, c, f, t in rows
        ]

    async def top_skus(
        self, start: date, end: date, *, customer_id: int | None = None
    ) -> list[SkuCount]:
        stmt = (
            select(
                OrderAuditModel.sku,
                func.max(OrderAuditModel.description),
                func.count(),
            )
            .where(
                *_in_range(start, end, customer_id),
                OrderAuditModel.event == EVENT_CREATED,
                OrderAuditModel.sku.is_not(None),
            )
            .group_by(OrderAuditModel.sku)
            .order_by(func.count().desc())
        )
        rows = (await self._session.execute(stmt)).all()
        return [SkuCount(sku=s, description=d, count=n) for s, d, n in rows]

    async def top_devices(
        self, start: date, end: date, customer_id: int, limit: int
    ) -> list[DeviceCount]:
        stmt = (
            select(OrderAuditModel.device_serial, func.count())
            .where(
                *_in_range(start, end, customer_id),
                OrderAuditModel.event == EVENT_CREATED,
                OrderAuditModel.device_serial.is_not(None),
                OrderAuditModel.device_serial != "",
            )
            .group_by(OrderAuditModel.device_serial)
            .order_by(func.count().desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [DeviceCount(device_serial=serial, count=n) for serial, n in rows]

    async def failure_reasons(
        self, start: date, end: date, customer_id: int, limit: int
    ) -> list[FailureReasonCount]:
        reason = func.coalesce(func.nullif(OrderAuditModel.detail, ""), _NO_DETAIL)
        stmt = (
            select(reason, func.count(), func.max(OrderAuditModel.created_at))
            .where(
                *_in_range(start, end, customer_id),
                OrderAuditModel.event == EVENT_FAILED,
            )
            .group_by(reason)
            .order_by(func.count().desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [FailureReasonCount(reason=r, count=n, last_at=at) for r, n, at in rows]

    async def recent_failures(
        self, start: date, end: date, customer_id: int, limit: int
    ) -> list[RecentFailure]:
        stmt = (
            select(
                OrderAuditModel.created_at,
                OrderAuditModel.sku,
                OrderAuditModel.device_serial,
                OrderAuditModel.detail,
            )
            .where(
                *_in_range(start, end, customer_id),
                OrderAuditModel.event == EVENT_FAILED,
            )
            .order_by(OrderAuditModel.id.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            RecentFailure(created_at=at, sku=sku, device_serial=serial, detail=detail)
            for at, sku, serial, detail in rows
        ]

    async def source_split(self, start: date, end: date, customer_id: int) -> SourceSplit:
        auto = func.sum(case((OrderAuditModel.detail.like(_AUTOLOAD_MARK), 1), else_=0))
        stmt = select(auto, func.count()).where(
            *_in_range(start, end, customer_id),
            OrderAuditModel.event == EVENT_CREATED,
        )
        auto_count, total = (await self._session.execute(stmt)).one()
        return SourceSplit(auto=auto_count or 0, total=total or 0)

    async def fulfillment_rows(
        self, start: date, end: date, customer_id: int
    ) -> list[FulfillmentRow]:
        stmt = (
            select(
                OrderAuditModel.sku,
                OrderAuditModel.device_serial,
                OrderAuditModel.hp_request_time,
                OrderAuditModel.created_at,
            )
            .where(
                *_in_range(start, end, customer_id),
                OrderAuditModel.event == EVENT_CREATED,
                OrderAuditModel.hp_request_time.is_not(None),
            )
            .order_by(OrderAuditModel.id)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            FulfillmentRow(
                sku=sku, device_serial=serial, hp_request_time=asked, created_at=loaded
            )
            for sku, serial, asked, loaded in rows
        ]

    async def dispatch_rows(
        self, start: date, end: date, customer_id: int
    ) -> list[DispatchRow]:
        stmt = (
            select(
                OrderAuditModel.sku,
                OrderAuditModel.device_serial,
                OrderAuditModel.internal_order_id,
                OrderAuditModel.created_at,
            )
            .where(
                *_in_range(start, end, customer_id),
                OrderAuditModel.event == EVENT_CREATED,
                OrderAuditModel.order_type == ORDER_TYPE_SUPPLY,
                OrderAuditModel.internal_order_id.is_not(None),
                OrderAuditModel.internal_order_id.not_like(_DRYRUN_PREFIX),
            )
            .order_by(OrderAuditModel.id)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            DispatchRow(
                sku=sku, device_serial=serial, internal_order_id=oid, created_at=at
            )
            for sku, serial, oid, at in rows
        ]
