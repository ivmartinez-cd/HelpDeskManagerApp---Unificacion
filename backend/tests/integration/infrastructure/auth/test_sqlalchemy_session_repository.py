import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.session import Session
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.value_objects.email import Email
from src.modules.auth.domain.value_objects.password_hash import PasswordHash
from src.modules.auth.infrastructure.repositories.sqlalchemy_session_repository import (
    SqlAlchemySessionRepository,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)

_NOW = datetime.now(UTC)


async def _persist_user(db_session: AsyncSession) -> uuid.UUID:
    user = User(
        id=uuid.uuid4(),
        email=Email("user@example.com"),
        password_hash=PasswordHash("$argon2id$fake"),
        full_name="Ada Lovelace",
        is_active=True,
        is_superadmin=False,
        created_at=_NOW,
    )
    await SqlAlchemyUserRepository(db_session).add(user)
    return user.id


def _build_session(user_id: uuid.UUID, token_hash: bytes = b"hash-a") -> Session:
    return Session(
        id=uuid.uuid4(),
        user_id=user_id,
        token_hash=token_hash,
        issued_at=_NOW,
        expires_at=_NOW + timedelta(days=7),
        last_seen_at=_NOW,
    )


async def test_add_then_get_by_token_hash_round_trips(db_session: AsyncSession) -> None:
    user_id = await _persist_user(db_session)
    repo = SqlAlchemySessionRepository(db_session)
    session = _build_session(user_id)

    await repo.add(session)
    found = await repo.get_by_token_hash(b"hash-a")

    assert found is not None
    assert found.user_id == user_id


async def test_get_by_token_hash_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SqlAlchemySessionRepository(db_session)

    assert await repo.get_by_token_hash(b"never-issued") is None


async def test_save_persists_revocation(db_session: AsyncSession) -> None:
    user_id = await _persist_user(db_session)
    repo = SqlAlchemySessionRepository(db_session)
    session = _build_session(user_id)
    await repo.add(session)

    session.revoke(at=_NOW + timedelta(minutes=1))
    await repo.save(session)

    found = await repo.get_by_token_hash(b"hash-a")
    assert found is not None
    assert found.revoked_at is not None


async def test_revoke_all_for_user_revokes_every_active_session(db_session: AsyncSession) -> None:
    user_id = await _persist_user(db_session)
    repo = SqlAlchemySessionRepository(db_session)
    await repo.add(_build_session(user_id, b"hash-a"))
    await repo.add(_build_session(user_id, b"hash-b"))

    await repo.revoke_all_for_user(user_id, at=_NOW + timedelta(minutes=1))

    first = await repo.get_by_token_hash(b"hash-a")
    second = await repo.get_by_token_hash(b"hash-b")
    assert first is not None and first.revoked_at is not None
    assert second is not None and second.revoked_at is not None
