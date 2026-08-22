"""Implementación Postgres del puerto AuditStatisticsRepository.

Las consultas viven en `_audit_statistics_queries` (toda la agregación en SQL, nunca
contar filas crudas en Python); acá solo se ejecutan y se mapean a los value objects.
"""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

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
from src.modules.insumos.infrastructure.repositories import _audit_statistics_queries as q
from src.modules.insumos.infrastructure.repositories._audit_statistics_queries import StatsScope


class SqlAlchemyAuditStatisticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def earliest_day(self) -> date | None:
        return (await self._session.execute(q.earliest_day_query())).scalars().first()

    async def customer_name(self, customer_id: int) -> str | None:
        stmt = q.customer_name_query(customer_id)
        return (await self._session.execute(stmt)).scalars().first()

    async def daily_counts(
        self, start: date, end: date, *, customer_id: int | None = None
    ) -> list[DailyEventCount]:
        stmt = q.daily_counts_query(StatsScope(start, end, customer_id))
        rows = (await self._session.execute(stmt)).all()
        return [DailyEventCount(day=d, event=e, count=n) for d, e, n in rows]

    async def event_totals(
        self, start: date, end: date, *, customer_id: int | None = None
    ) -> dict[str, int]:
        stmt = q.event_totals_query(StatsScope(start, end, customer_id))
        rows = (await self._session.execute(stmt)).all()
        return {event: total for event, total in rows}

    async def customer_activity(self, start: date, end: date) -> list[CustomerActivity]:
        stmt = q.customer_activity_query(StatsScope(start, end))
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
        stmt = q.top_skus_query(StatsScope(start, end, customer_id))
        rows = (await self._session.execute(stmt)).all()
        return [SkuCount(sku=s, description=d, count=n) for s, d, n in rows]

    async def top_devices(
        self, start: date, end: date, customer_id: int, limit: int
    ) -> list[DeviceCount]:
        stmt = q.top_devices_query(StatsScope(start, end, customer_id), limit)
        rows = (await self._session.execute(stmt)).all()
        return [DeviceCount(device_serial=serial, count=n) for serial, n in rows]

    async def failure_reasons(
        self, start: date, end: date, customer_id: int, limit: int
    ) -> list[FailureReasonCount]:
        stmt = q.failure_reasons_query(StatsScope(start, end, customer_id), limit)
        rows = (await self._session.execute(stmt)).all()
        return [FailureReasonCount(reason=r, count=n, last_at=at) for r, n, at in rows]

    async def recent_failures(
        self, start: date, end: date, customer_id: int, limit: int
    ) -> list[RecentFailure]:
        stmt = q.recent_failures_query(StatsScope(start, end, customer_id), limit)
        rows = (await self._session.execute(stmt)).all()
        return [
            RecentFailure(created_at=at, sku=sku, device_serial=serial, detail=detail)
            for at, sku, serial, detail in rows
        ]

    async def source_split(self, start: date, end: date, customer_id: int) -> SourceSplit:
        stmt = q.source_split_query(StatsScope(start, end, customer_id))
        auto_count, total = (await self._session.execute(stmt)).one()
        return SourceSplit(auto=auto_count or 0, total=total or 0)

    async def fulfillment_rows(
        self, start: date, end: date, customer_id: int
    ) -> list[FulfillmentRow]:
        stmt = q.fulfillment_rows_query(StatsScope(start, end, customer_id))
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
        stmt = q.dispatch_rows_query(StatsScope(start, end, customer_id))
        rows = (await self._session.execute(stmt)).all()
        return [
            DispatchRow(
                sku=sku, device_serial=serial, internal_order_id=oid, created_at=at
            )
            for sku, serial, oid, at in rows
        ]
