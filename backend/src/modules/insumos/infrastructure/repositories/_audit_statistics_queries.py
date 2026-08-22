"""Consultas SQL de SqlAlchemyAuditStatisticsRepository — solo construyen el `Select`.

Toda la agregación vive en SQL (GROUP BY / SUM / COUNT) — nunca se traen las filas
crudas para contarlas en Python. Las dos únicas excepciones son fulfillment_rows y
dispatch_rows, que devuelven filas porque su cálculo depende de horario laboral y de
supply_status_history, no de una agregación expresable en la misma query.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import ColumnElement, Select, case, func, select

from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CREATED,
    EVENT_FAILED,
    ORDER_TYPE_SUPPLY,
)
from src.modules.insumos.infrastructure.models.order_audit_model import OrderAuditModel
from src.modules.insumos.infrastructure.repositories._argentina_day import argentina_day

_AUDITED_EVENTS = (EVENT_CREATED, EVENT_FAILED)
_NO_DETAIL = "Sin detalle"
# El detalle de auto-carga tiene variantes ("Pre-Correctivo (kit de mantenimiento) —
# Auto-carga"), por eso se busca la subcadena y no el valor exacto.
_AUTOLOAD_MARK = "%Auto-carga%"
_DRYRUN_PREFIX = "DRYRUN%"


@dataclass(frozen=True)
class StatsScope:
    """Rango de días (argentinos, inclusive) y cliente opcional de una consulta."""

    start: date
    end: date
    customer_id: int | None = None


def _day() -> ColumnElement[date]:
    return argentina_day(OrderAuditModel.created_at)


def _in_range(scope: StatsScope) -> list[ColumnElement[bool]]:
    filters = [OrderAuditModel.dry_run.is_(False), _day() >= scope.start, _day() <= scope.end]
    if scope.customer_id is not None:
        filters.append(OrderAuditModel.customer_id == scope.customer_id)
    return filters


def _count_of(event: str) -> ColumnElement[int]:
    return func.sum(case((OrderAuditModel.event == event, 1), else_=0))


def earliest_day_query() -> Select[Any]:
    return select(func.min(_day())).where(OrderAuditModel.dry_run.is_(False))


def customer_name_query(customer_id: int) -> Select[Any]:
    return (
        select(OrderAuditModel.customer_name)
        .where(
            OrderAuditModel.customer_id == customer_id,
            OrderAuditModel.customer_name.is_not(None),
            OrderAuditModel.customer_name != "",
        )
        .order_by(OrderAuditModel.id.desc())
        .limit(1)
    )


def daily_counts_query(scope: StatsScope) -> Select[Any]:
    day = _day()
    return (
        select(day, OrderAuditModel.event, func.count())
        .where(*_in_range(scope), OrderAuditModel.event.in_(_AUDITED_EVENTS))
        .group_by(day, OrderAuditModel.event)
        .order_by(day)
    )


def event_totals_query(scope: StatsScope) -> Select[Any]:
    return (
        select(OrderAuditModel.event, func.count())
        .where(*_in_range(scope), OrderAuditModel.event.in_(_AUDITED_EVENTS))
        .group_by(OrderAuditModel.event)
    )


def customer_activity_query(scope: StatsScope) -> Select[Any]:
    return (
        select(
            OrderAuditModel.customer_id,
            func.max(OrderAuditModel.customer_name),
            _count_of(EVENT_CREATED),
            _count_of(EVENT_FAILED),
            func.count(),
        )
        .where(
            *_in_range(scope),
            OrderAuditModel.event.in_(_AUDITED_EVENTS),
            # Sin cliente no hay a quién rankear (eventos del sistema).
            OrderAuditModel.customer_id.is_not(None),
        )
        .group_by(OrderAuditModel.customer_id)
        .order_by(func.count().desc())
    )


def top_skus_query(scope: StatsScope) -> Select[Any]:
    return (
        select(OrderAuditModel.sku, func.max(OrderAuditModel.description), func.count())
        .where(
            *_in_range(scope),
            OrderAuditModel.event == EVENT_CREATED,
            OrderAuditModel.sku.is_not(None),
        )
        .group_by(OrderAuditModel.sku)
        .order_by(func.count().desc())
    )


def top_devices_query(scope: StatsScope, limit: int) -> Select[Any]:
    return (
        select(OrderAuditModel.device_serial, func.count())
        .where(
            *_in_range(scope),
            OrderAuditModel.event == EVENT_CREATED,
            OrderAuditModel.device_serial.is_not(None),
            OrderAuditModel.device_serial != "",
        )
        .group_by(OrderAuditModel.device_serial)
        .order_by(func.count().desc())
        .limit(limit)
    )


def failure_reasons_query(scope: StatsScope, limit: int) -> Select[Any]:
    reason = func.coalesce(func.nullif(OrderAuditModel.detail, ""), _NO_DETAIL)
    return (
        select(reason, func.count(), func.max(OrderAuditModel.created_at))
        .where(*_in_range(scope), OrderAuditModel.event == EVENT_FAILED)
        .group_by(reason)
        .order_by(func.count().desc())
        .limit(limit)
    )


def recent_failures_query(scope: StatsScope, limit: int) -> Select[Any]:
    return (
        select(
            OrderAuditModel.created_at,
            OrderAuditModel.sku,
            OrderAuditModel.device_serial,
            OrderAuditModel.detail,
        )
        .where(*_in_range(scope), OrderAuditModel.event == EVENT_FAILED)
        .order_by(OrderAuditModel.id.desc())
        .limit(limit)
    )


def source_split_query(scope: StatsScope) -> Select[Any]:
    auto = func.sum(case((OrderAuditModel.detail.like(_AUTOLOAD_MARK), 1), else_=0))
    return select(auto, func.count()).where(
        *_in_range(scope), OrderAuditModel.event == EVENT_CREATED
    )


def fulfillment_rows_query(scope: StatsScope) -> Select[Any]:
    return (
        select(
            OrderAuditModel.sku,
            OrderAuditModel.device_serial,
            OrderAuditModel.hp_request_time,
            OrderAuditModel.created_at,
        )
        .where(
            *_in_range(scope),
            OrderAuditModel.event == EVENT_CREATED,
            OrderAuditModel.hp_request_time.is_not(None),
        )
        .order_by(OrderAuditModel.id)
    )


def dispatch_rows_query(scope: StatsScope) -> Select[Any]:
    return (
        select(
            OrderAuditModel.sku,
            OrderAuditModel.device_serial,
            OrderAuditModel.internal_order_id,
            OrderAuditModel.created_at,
        )
        .where(
            *_in_range(scope),
            OrderAuditModel.event == EVENT_CREATED,
            OrderAuditModel.order_type == ORDER_TYPE_SUPPLY,
            OrderAuditModel.internal_order_id.is_not(None),
            OrderAuditModel.internal_order_id.not_like(_DRYRUN_PREFIX),
        )
        .order_by(OrderAuditModel.id)
    )
