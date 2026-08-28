"""Tests de integración de SqlAlchemyProcessedRequestRepository (Postgres de test)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.processed_request import (
    STATUS_CANCELLED,
    STATUS_CREATED,
    ProcessedInitialSnapshot,
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


async def test_get_all_created_filtra_por_cliente_y_status(db_session: AsyncSession) -> None:
    repo = SqlAlchemyProcessedRequestRepository(db_session)
    await repo.mark_processed(_request(974325))
    await repo.mark_processed(_request(974326, customer_id=9, internal_order_id="441771-1"))
    await repo.mark_processed(_request(974327, status=STATUS_CANCELLED))

    todos = await repo.get_all_created()
    del_cliente = await repo.get_all_created(customer_id=9)

    assert {r.hp_request_id for r in todos} == {974325, 974326}
    assert [r.hp_request_id for r in del_cliente] == [974326]


async def test_backfill_initial_snapshot_completa_filas_existentes(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyProcessedRequestRepository(db_session)
    await repo.mark_processed(_request(initial_percent_left=None, initial_days_left=None))

    await repo.backfill_initial_snapshot(
        [
            ProcessedInitialSnapshot(
                hp_request_id=974325,
                initial_percent_left=9,
                initial_days_left=3,
                initial_pages_left=None,
            )
        ]
    )

    row = await repo.get(974325)
    assert row is not None
    assert row.initial_percent_left == 9
    assert row.initial_days_left == 3


async def test_consumable_serial_se_persiste_y_se_lee(db_session: AsyncSession) -> None:
    repo = SqlAlchemyProcessedRequestRepository(db_session)
    await repo.mark_processed(
        _request(consumable_serial="CRUM-0000-6917", consumable_colour="CYAN")
    )

    row = await repo.get(974325)

    assert row is not None
    assert row.consumable_serial == "CRUM-0000-6917"
    assert row.consumable_colour == "CYAN"


async def test_get_missing_consumable_serial_solo_trae_created_sin_serie(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyProcessedRequestRepository(db_session)
    await repo.mark_processed(_request(974325, consumable_serial=None))
    await repo.mark_processed(_request(974326, consumable_serial="CRUM-1"))
    await repo.mark_processed(_request(974327, status=STATUS_CANCELLED, consumable_serial=None))

    missing = await repo.get_missing_consumable_serial()

    assert [r.hp_request_id for r in missing] == [974325]


async def test_get_missing_consumable_serial_respeta_within_days(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyProcessedRequestRepository(db_session)
    await repo.mark_processed(_request(974325, consumable_serial=None))
    old_created_at = datetime.now(UTC) - timedelta(days=30)
    await db_session.execute(
        update(ProcessedRequestModel)
        .where(ProcessedRequestModel.hp_request_id == 974325)
        .values(created_at=old_created_at)
    )
    await db_session.flush()

    missing = await repo.get_missing_consumable_serial(within_days=7)

    assert missing == []


async def test_backfill_consumable_serial_completa_filas_existentes(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyProcessedRequestRepository(db_session)
    await repo.mark_processed(_request(consumable_serial=None))

    await repo.backfill_consumable_serial([(974325, "CRUM-0000-6917")])

    row = await repo.get(974325)
    assert row is not None
    assert row.consumable_serial == "CRUM-0000-6917"


async def test_find_consumable_serial_reuse_batch_agrupa_por_serie(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyProcessedRequestRepository(db_session)
    await repo.mark_processed(
        _request(974325, device_serial="SERIE1", consumable_serial="CRUM-1")
    )
    await repo.mark_processed(
        _request(974326, device_serial="SERIE2", consumable_serial="CRUM-1")
    )
    await repo.mark_processed(
        _request(974327, device_serial="SERIE1", consumable_serial="CRUM-2")
    )

    result = await repo.find_consumable_serial_reuse_batch({"crum-1"})

    assert {r.hp_request_id for r in result["CRUM-1"]} == {974325, 974326}
    assert "CRUM-2" not in result
