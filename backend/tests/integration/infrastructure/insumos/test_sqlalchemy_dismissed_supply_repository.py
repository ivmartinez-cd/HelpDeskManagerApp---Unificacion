"""Tests de integración de SqlAlchemyDismissedSupplyRepository (Postgres de test)."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.infrastructure.repositories.sqlalchemy_dismissed_supply_repository import (  # noqa: E501
    SqlAlchemyDismissedSupplyRepository,
)


async def test_mark_dismissed_es_idempotente(db_session: AsyncSession) -> None:
    repo = SqlAlchemyDismissedSupplyRepository(db_session)

    await repo.mark_dismissed(442759, "SERIE1", hp_request_id=974325)
    await repo.mark_dismissed(442759, "SERIE1", hp_request_id=974325)

    assert await repo.get_all_dismissed_ids() == {442759}


async def test_get_dismissed_ids_es_batch(db_session: AsyncSession) -> None:
    repo = SqlAlchemyDismissedSupplyRepository(db_session)
    await repo.mark_dismissed(442759, "SERIE1")
    await repo.mark_dismissed(442760, "SERIE2")

    assert await repo.get_dismissed_ids([442759, 999999]) == {442759}


async def test_get_pending_unignore_solo_trae_hp_request_id_no_nulo(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyDismissedSupplyRepository(db_session)
    await repo.mark_dismissed(442759, "SERIE1", hp_request_id=974325)  # dismiss temporal
    await repo.mark_dismissed(442760, "SERIE2", hp_request_id=None)  # ignore permanente

    pending = await repo.get_pending_unignore()

    assert [p.supply_id for p in pending] == [442759]
    assert pending[0].hp_request_id == 974325


async def test_clear_saca_el_descarte(db_session: AsyncSession) -> None:
    repo = SqlAlchemyDismissedSupplyRepository(db_session)
    await repo.mark_dismissed(442759, "SERIE1", hp_request_id=974325)

    await repo.clear(442759)

    assert await repo.get_all_dismissed_ids() == set()
