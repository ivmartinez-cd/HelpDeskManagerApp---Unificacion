"""Tests de integración de los métodos batch que alimentan el dashboard."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.processed_request import (
    STATUS_CANCELLED,
    STATUS_CREATED,
    ProcessedRequest,
)
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply
from src.modules.insumos.infrastructure.models.app_setting_model import AppSettingModel
from src.modules.insumos.infrastructure.models.customer_config_model import CustomerConfigModel
from src.modules.insumos.infrastructure.models.request_validation_model import (
    RequestValidationModel,
)
from src.modules.insumos.infrastructure.models.supply_serial_cache_model import (
    SupplySerialCacheModel,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_customer_config_repository import (  # noqa: E501
    SqlAlchemyCustomerConfigRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_insumos_settings_repository import (  # noqa: E501
    SqlAlchemyInsumosSettingsRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_processed_request_repository import (  # noqa: E501
    SqlAlchemyProcessedRequestRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_request_validation_repository import (  # noqa: E501
    SqlAlchemyRequestValidationRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_supply_cache_repository import (
    SqlAlchemySupplyCacheRepository,
)


def _processed(hp_request_id: int, **overrides: object) -> ProcessedRequest:
    base: dict[str, object] = {
        "hp_request_id": hp_request_id,
        "device_serial": "SERIE1",
        "sku": "CF230A",
        "internal_order_id": f"{440000 + hp_request_id}-1",
        "status": STATUS_CREATED,
    }
    base.update(overrides)
    return ProcessedRequest(**base)  # type: ignore[arg-type]


async def test_processed_batches(db_session: AsyncSession) -> None:
    repo = SqlAlchemyProcessedRequestRepository(db_session)
    await repo.mark_processed(_processed(1))
    await repo.mark_processed(_processed(2, internal_order_id="DRYRUN-SDS-2"))
    await repo.mark_processed(_processed(3, status=STATUS_CANCELLED))

    assert await repo.get_processed_ids([1, 2, 3, 99]) == {1, 2}
    assert await repo.get_supply_ids([1, 2, 3]) == {1: 440001}  # DRYRUN y CANCELLED afuera
    assert await repo.get_today_processed_ids([1, 2, 3]) == {1, 2}
    assert await repo.count_processed_today() == 2
    by_serial = await repo.get_created_by_serials(["serie1"])
    assert {r.hp_request_id for r in by_serial["SERIE1"]} == {1, 2}


async def test_supply_cache_batches(db_session: AsyncSession) -> None:
    repo = SqlAlchemySupplyCacheRepository(db_session)
    await repo.upsert(
        [
            CachedSupply(supply_id=111, serial="SERIE1", estado="Pendiente"),
            CachedSupply(supply_id=222, serial="SERIE1", estado="Anulado"),
            CachedSupply(supply_id=333, serial="OTRA", estado="Entregado"),
        ]
    )

    assert await repo.get_statuses_batch([111, 222, 999]) == {111: "Pendiente", 222: "Anulado"}
    # Recién cacheados: ambos entran en la ventana; una fila envejecida a mano queda fuera.
    assert await repo.get_recently_cached_ids([111, 222], within_seconds=3600) == {111, 222}
    await db_session.execute(
        update(SupplySerialCacheModel)
        .where(SupplySerialCacheModel.supply_id == 111)
        .values(cached_at=datetime.now(UTC) - timedelta(hours=2))
    )
    assert await repo.get_recently_cached_ids([111, 222], within_seconds=3600) == {222}

    by_serial = await repo.get_noncancelled_by_serials(["serie1", "otra"])
    assert [s.supply_id for s in by_serial["SERIE1"]] == [111]  # Anulado excluido
    assert [s.supply_id for s in by_serial["OTRA"]] == [333]  # Entregado sí aparece


async def test_validation_pending_ids(db_session: AsyncSession) -> None:
    for rid, status in ((1, "PENDING"), (2, "DISMISSED")):
        db_session.add(
            RequestValidationModel(
                hp_request_id=rid,
                customer_id=8,
                device_id=7,
                device_serial="SERIE1",
                sku="CF230A",
                deadline_at=datetime.now(UTC),
                status=status,
            )
        )
    await db_session.flush()

    repo = SqlAlchemyRequestValidationRepository(db_session)
    assert await repo.get_pending_ids([1, 2, 3]) == {1}


async def test_customer_config_list_enabled(db_session: AsyncSession) -> None:
    db_session.add(CustomerConfigModel(customer_id=8, name="Zeta", enabled=True))
    db_session.add(CustomerConfigModel(customer_id=9, name="Alfa", enabled=True))
    db_session.add(CustomerConfigModel(customer_id=10, name="Apagado", enabled=False))
    await db_session.flush()

    repo = SqlAlchemyCustomerConfigRepository(db_session)
    customers = await repo.list_enabled()

    assert [c.name for c in customers] == ["Alfa", "Zeta"]


async def test_settings_get_all(db_session: AsyncSession) -> None:
    db_session.add(AppSettingModel(key="threshold_critical", value="5"))
    await db_session.flush()

    repo = SqlAlchemyInsumosSettingsRepository(db_session)
    assert await repo.get_all() == {"threshold_critical": "5"}
