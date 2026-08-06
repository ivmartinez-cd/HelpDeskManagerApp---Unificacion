import uuid
from datetime import UTC, datetime, timedelta

from src.modules.auth.domain.entities.password_reset_token import PasswordResetToken

_ISSUED = datetime(2026, 1, 1, tzinfo=UTC)
_EXPIRES = _ISSUED + timedelta(minutes=30)


def _build_token() -> PasswordResetToken:
    return PasswordResetToken(
        id=uuid.uuid4(), user_id=uuid.uuid4(), token_hash=b"hash", expires_at=_EXPIRES
    )


def test_is_usable_before_expiry_and_unused() -> None:
    token = _build_token()

    assert token.is_usable(at=_ISSUED + timedelta(minutes=5)) is True


def test_is_not_usable_once_expired() -> None:
    token = _build_token()

    assert token.is_usable(at=_EXPIRES + timedelta(seconds=1)) is False


def test_is_not_usable_once_marked_used_even_if_not_expired() -> None:
    token = _build_token()

    token.used_at = _ISSUED + timedelta(minutes=1)

    assert token.is_usable(at=_ISSUED + timedelta(minutes=2)) is False


def test_equality_is_based_on_identity() -> None:
    shared_id = uuid.uuid4()
    a = PasswordResetToken(
        id=shared_id, user_id=uuid.uuid4(), token_hash=b"a", expires_at=_EXPIRES
    )
    b = PasswordResetToken(
        id=shared_id, user_id=uuid.uuid4(), token_hash=b"b", expires_at=_EXPIRES
    )

    assert a == b
    assert hash(a) == hash(b)
