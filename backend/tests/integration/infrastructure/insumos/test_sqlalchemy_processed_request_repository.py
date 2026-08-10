"""Tests de integración de SqlAlchemyProcessedRequestRepository (Postgres de test)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.processed_request import (
    STATUS_CANCELLED,
    STATUS_CREATED,
    ProcessedRequest,
)
from src.modules.insumos.infrastructure.models.processed_request_model import (
    ProcessedRequestModel,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_processed_request_repository import (  # noqa: E501
    SqlAlchemyProcessedRequestRepository,
)


def _request(hp_request_id: int = 974325, **overrides: object) -> ProcessedRequest:
    base: dict[str, object] = {
        "hp_request_id": hp_request_id,
        "device_id": 7,
        "device_serial": "SERIE1",
        "customer_id": 8,
        "sku": "CF230A",
        "internal_order_id": "441770-3",
        "status": STATUS_CREATED,
        "description": "Toner HP 30A",
    }
    base.update(overrides)
    return ProcessedRequest(**base)  # type: ignore[arg-type]


async def test_mark_processed_y_get(db_session: AsyncSession) -> None:
    repo = SqlAlchemyProcessedRequestRepository(db_session)
    await repo.mark_processed(_request())

    row = await repo.get(974325)

    assert row is not None
    assert row.status == STATUS_CREATED
    assert row.internal_order_id == "441770-3"


async def test_mark_processed_es_upsert(db_session: AsyncSession) -> None:
    repo = SqlAlchemyProcessedRequestRepository(db_session)
    await repo.mark_processed(_request(internal_order_id="441770-3"))
    await repo.mark_processed(_request(internal_order_id="441999-1"))

    row = await repo.get(974325)

    assert row is not None
    assert row.internal_order_id == "441999-1"


async def test_mark_cancelled_no_borra_la_fila(db_session: AsyncSession) -> None:
    repo = SqlAlchemyProcessedRequestRepository(db_session)
    await repo.mark_processed(_request())

    await repo.mark_cancelled(974325)

    row = await repo.get(974325)
    assert row is not None
    assert row.status == STATUS_CANCELLED


async def test_get_today_order_for_solo_ve_el_dia_argentino(db_session: AsyncSession) -> None:
    repo = SqlAlchemyProcessedRequestRepository(db_session)
    await repo.mark_processed(_request())

    assert await repo.get_today_order_for("SERIE1", "CF230A") is not None

    # Un pedido de hace 3 días no cuenta como "hoy".
    await db_session.execute(
        update(ProcessedRequestModel)
        .where(ProcessedRequestModel.hp_request_id == 974325)
        .values(created_at=datetime.now(UTC) - timedelta(days=3))
    )
    assert await repo.get_today_order_for("SERIE1", "CF230A") is None


async def test_get_today_order_for_ignora_cancelados(db_session: AsyncSession) -> None:
    repo = SqlAlchemyProcessedRequestRepository(db_session)
    await repo.mark_processed(_request(status=STATUS_CANCELLED))

    assert await repo.get_today_order_for("SERIE1", "CF230A") is None


async def test_get_created_by_serial_es_case_insensitive(db_session: AsyncSession) -> None:
    repo = SqlAlchemyProcessedRequestRepository(db_session)
    await repo.mark_processed(_request(974325))
    await repo.mark_processed(_request(974326, internal_order_id="441771-1"))
    await repo.mark_processed(_request(974327, status=STATUS_CANCELLED))

    rows = await repo.get_created_by_serial("serie1")

    assert len(rows) == 2
    assert all(r.status == STATUS_CREATED for r in rows)
