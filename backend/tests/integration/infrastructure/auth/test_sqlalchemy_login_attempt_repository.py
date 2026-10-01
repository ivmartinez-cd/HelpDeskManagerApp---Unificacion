from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.repositories.sqlalchemy_login_attempt_repository import (
    SqlAlchemyLoginAttemptRepository,
)

_NOW = datetime.now(UTC)


async def test_counts_only_recent_failures_for_the_given_email(db_session: AsyncSession) -> None:
    repo = SqlAlchemyLoginAttemptRepository(db_session)
    await repo.record(email="a@example.com", ip="127.0.0.1", succeeded=False)
    await repo.record(email="a@example.com", ip="127.0.0.1", succeeded=False)
    await repo.record(email="a@example.com", ip="127.0.0.1", succeeded=True)
    await repo.record(email="b@example.com", ip="127.0.0.1", succeeded=False)

    count = await repo.count_recent_failures(email="a@example.com", since=_NOW - timedelta(hours=1))

    assert count == 2


async def test_does_not_count_failures_before_the_since_cutoff(db_session: AsyncSession) -> None:
    repo = SqlAlchemyLoginAttemptRepository(db_session)
    await repo.record(email="a@example.com", ip=None, succeeded=False)

    count = await repo.count_recent_failures(
        email="a@example.com", since=_NOW + timedelta(hours=1)
    )

    assert count == 0


async def test_mark_succeeded_saca_el_intento_de_los_fallos(db_session: AsyncSession) -> None:
    repo = SqlAlchemyLoginAttemptRepository(db_session)
    attempt_id = await repo.record(email="a@example.com", ip=None, succeeded=False)

    await repo.mark_succeeded(attempt_id)

    since = _NOW - timedelta(hours=1)
    assert await repo.count_recent_failures(email="a@example.com", since=since) == 0
