import uuid
from datetime import UTC, datetime

from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.value_objects.email import Email
from src.modules.auth.domain.value_objects.password_hash import PasswordHash


def _build_user(user_id: uuid.UUID, email: str = "user@example.com") -> User:
    return User(
        id=user_id,
        email=Email(email),
        password_hash=PasswordHash("$argon2id$..."),
        full_name="Ada Lovelace",
        is_active=True,
        is_superadmin=False,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_equality_is_based_on_identity_not_on_field_values() -> None:
    shared_id = uuid.uuid4()
    same_identity = _build_user(shared_id, "one@example.com")
    same_identity_different_fields = _build_user(shared_id, "other@example.com")
    different_identity = _build_user(uuid.uuid4(), "one@example.com")

    assert same_identity == same_identity_different_fields
    assert same_identity != different_identity


def test_hash_is_consistent_with_equality() -> None:
    shared_id = uuid.uuid4()
    a = _build_user(shared_id)
    b = _build_user(shared_id)

    assert hash(a) == hash(b)
