"""Tests de integración de SqlAlchemyOrderClaimRepository contra Postgres real."""
import asyncio

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.modules.insumos.infrastructure.models.order_claim_model import OrderClaimModel
from src.modules.insumos.infrastructure.repositories.sqlalchemy_order_claim_repository import (
    SqlAlchemyOrderClaimRepository,
)


async def test_try_claim_then_release_then_try_claim_again_succeeds(db_session) -> None:
    repo = SqlAlchemyOrderClaimRepository(db_session)

    assert await repo.try_claim("SER1", "SKU1") is True
    assert await repo.try_claim("SER1", "SKU1") is False  # ya hay uno IN_PROGRESS

    await repo.release("SER1", "SKU1")

    assert await repo.try_claim("SER1", "SKU1") is True  # el anterior quedó DONE, no bloquea


async def test_try_claim_is_independent_per_serial_sku(db_session) -> None:
    repo = SqlAlchemyOrderClaimRepository(db_session)

    assert await repo.try_claim("SER1", "SKU1") is True
    assert await repo.try_claim("SER1", "SKU2") is True  # mismo serial, otro sku
    assert await repo.try_claim("SER2", "SKU1") is True  # mismo sku, otro serial


async def test_release_is_idempotent_when_nothing_is_claimed(db_session) -> None:
    repo = SqlAlchemyOrderClaimRepository(db_session)

    await repo.release("SER-SIN-CLAIM", "SKU1")  # no debe lanzar


async def test_try_claim_only_one_winner_under_real_concurrency(
    _test_engine: AsyncEngine,
) -> None:
    """A diferencia de los tests de arriba, este NO usa el fixture
    `db_session` (comparte una única transacción con savepoints por test,
    no sirve para probar concurrencia real entre dos procesos). Acá se
    abren dos sesiones/transacciones genuinamente independientes — es la
    prueba concreta de la garantía que reemplaza a `KeyedLock`: que sea
    Postgres, no nuestro código, quien decida cuál de dos intentos
    simultáneos gana."""
    serial, sku = "SERIAL-CONCURRENCY-TEST", "SKU-CONCURRENCY-TEST"

    async def _claim() -> bool:
        async with AsyncSession(_test_engine, expire_on_commit=False) as session:
            won = await SqlAlchemyOrderClaimRepository(session).try_claim(serial, sku)
            await session.commit()
            return won

    try:
        results = await asyncio.gather(_claim(), _claim())
        assert sorted(results) == [False, True]
    finally:
        async with AsyncSession(_test_engine, expire_on_commit=False) as cleanup:
            await cleanup.execute(
                delete(OrderClaimModel).where(
                    OrderClaimModel.device_serial == serial, OrderClaimModel.sku == sku
                )
            )
            await cleanup.commit()
