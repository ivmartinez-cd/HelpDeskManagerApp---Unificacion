from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.domain.value_objects.meter_source import MeterSource
from src.modules.contadores.infrastructure.repositories.sqlalchemy_meter_client_config_repository import (  # noqa: E501
    SqlAlchemyMeterClientConfigRepository,
)


async def test_upsert_creates_a_new_row_when_none_exists(db_session: AsyncSession) -> None:
    repo = SqlAlchemyMeterClientConfigRepository(db_session)

    result = await repo.upsert(
        source=MeterSource("sds"), customer_id="123", customer_name="AGCO", suma_color=True
    )

    assert result.customer_name == "AGCO"
    assert result.suma_color is True


async def test_upsert_updates_the_existing_row_for_the_same_source_and_customer(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyMeterClientConfigRepository(db_session)
    await repo.upsert(
        source=MeterSource("sds"), customer_id="123", customer_name="AGCO", suma_color=False
    )

    updated = await repo.upsert(
        source=MeterSource("sds"), customer_id="123", customer_name="AGCO", suma_color=True
    )

    all_sds = await repo.list_by_source(MeterSource("sds"))
    assert len(all_sds) == 1
    assert updated.suma_color is True


async def test_same_customer_id_is_independent_across_sources(db_session: AsyncSession) -> None:
    repo = SqlAlchemyMeterClientConfigRepository(db_session)
    await repo.upsert(
        source=MeterSource("sds"), customer_id="123", customer_name="AGCO", suma_color=True
    )
    await repo.upsert(
        source=MeterSource("ers"), customer_id="123", customer_name="AGCO ERS", suma_color=False
    )

    sds_config = await repo.get(MeterSource("sds"), "123")
    ers_config = await repo.get(MeterSource("ers"), "123")

    assert sds_config is not None and sds_config.suma_color is True
    assert ers_config is not None and ers_config.suma_color is False


async def test_get_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SqlAlchemyMeterClientConfigRepository(db_session)

    assert await repo.get(MeterSource("sds"), "does-not-exist") is None
