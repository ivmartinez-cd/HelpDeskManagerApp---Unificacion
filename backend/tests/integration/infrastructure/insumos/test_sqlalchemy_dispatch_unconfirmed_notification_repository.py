"""Tests de integración de SqlAlchemyDispatchUnconfirmedNotificationRepository."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.infrastructure.repositories.sqlalchemy_dispatch_unconfirmed_notification_repository import (  # noqa: E501
    SqlAlchemyDispatchUnconfirmedNotificationRepository,
)


async def test_mark_notified_y_get_notified_ids(db_session: AsyncSession) -> None:
    repo = SqlAlchemyDispatchUnconfirmedNotificationRepository(db_session)

    await repo.mark_notified([974325, 974326])

    assert await repo.get_notified_ids([974325, 974326, 999999]) == {974325, 974326}


async def test_mark_notified_es_idempotente(db_session: AsyncSession) -> None:
    repo = SqlAlchemyDispatchUnconfirmedNotificationRepository(db_session)

    await repo.mark_notified([974325])
    await repo.mark_notified([974325])  # no debe romper (INSERT OR IGNORE)

    assert await repo.get_notified_ids([974325]) == {974325}
