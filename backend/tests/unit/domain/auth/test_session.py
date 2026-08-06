import uuid
from datetime import UTC, datetime, timedelta

from src.modules.auth.domain.entities.session import Session

_ISSUED = datetime(2026, 1, 1, tzinfo=UTC)
_EXPIRES = _ISSUED + timedelta(days=7)


def _build_session() -> Session:
    return Session(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        issued_at=_ISSUED,
        expires_at=_EXPIRES,
        last_seen_at=_ISSUED,
    )


def test_is_active_before_expiry_and_without_revocation() -> None:
    session = _build_session()

    assert session.is_active(at=_ISSUED + timedelta(hours=1)) is True


def test_is_not_active_once_expired() -> None:
    session = _build_session()

    assert session.is_active(at=_EXPIRES + timedelta(seconds=1)) is False


def test_is_not_active_once_revoked_even_if_not_expired() -> None:
    session = _build_session()

    session.revoke(at=_ISSUED + timedelta(minutes=5))

    assert session.is_active(at=_ISSUED + timedelta(minutes=10)) is False


def test_equality_is_based_on_identity() -> None:
    shared_id = uuid.uuid4()
    a = Session(
        id=shared_id, user_id=uuid.uuid4(), issued_at=_ISSUED, expires_at=_EXPIRES,
        last_seen_at=_ISSUED,
    )
    b = Session(
        id=shared_id, user_id=uuid.uuid4(), issued_at=_ISSUED, expires_at=_EXPIRES,
        last_seen_at=_ISSUED,
    )

    assert a == b
    assert hash(a) == hash(b)
