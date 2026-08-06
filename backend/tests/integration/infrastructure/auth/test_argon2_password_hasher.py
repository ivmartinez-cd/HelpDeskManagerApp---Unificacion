from argon2 import PasswordHasher as Argon2Hasher

from src.modules.auth.domain.value_objects.password_hash import PasswordHash
from src.modules.auth.domain.value_objects.raw_password import RawPassword
from src.modules.auth.infrastructure.argon2_password_hasher import Argon2PasswordHasher


def test_hash_then_verify_round_trips() -> None:
    hasher = Argon2PasswordHasher()
    raw = RawPassword("ValidPass123!")

    hashed = hasher.hash(raw)

    assert hasher.verify(raw, hashed) is True


def test_verify_rejects_the_wrong_password() -> None:
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash(RawPassword("ValidPass123!"))

    assert hasher.verify(RawPassword("OtroPass456!"), hashed) is False


def test_needs_rehash_is_false_for_a_hash_made_with_current_settings() -> None:
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash(RawPassword("ValidPass123!"))

    assert hasher.needs_rehash(hashed) is False


def test_needs_rehash_is_true_for_a_hash_made_with_weaker_parameters() -> None:
    hasher = Argon2PasswordHasher()
    weak_hash = PasswordHash(
        Argon2Hasher(time_cost=1, memory_cost=8, parallelism=1).hash("ValidPass123!")
    )

    assert hasher.needs_rehash(weak_hash) is True
