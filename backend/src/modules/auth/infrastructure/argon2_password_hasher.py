from functools import cache

from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError

from src.modules.auth.domain.value_objects.password_hash import PasswordHash
from src.modules.auth.domain.value_objects.raw_password import RawPassword
from src.shared.infrastructure.config.settings import get_settings


class Argon2PasswordHasher:
    """Implementa el puerto PasswordHasher. Parámetros desde Settings, nunca
    hardcodeados (bajarlos por debajo del default de la lib es un error de
    config, no algo que este adaptador deba permitir en silencio)."""

    def __init__(self) -> None:
        settings = get_settings()
        self._params = (
            settings.argon2_time_cost,
            settings.argon2_memory_cost_kib,
            settings.argon2_parallelism,
        )
        self._hasher = _build_hasher(*self._params)

    def hash(self, raw: RawPassword) -> PasswordHash:
        return PasswordHash(self._hasher.hash(raw.value))

    def verify(self, candidate: str, stored: PasswordHash) -> bool:
        try:
            return self._hasher.verify(stored.value, candidate)
        except VerifyMismatchError:
            return False

    def needs_rehash(self, stored: PasswordHash) -> bool:
        return self._hasher.check_needs_rehash(stored.value)

    def dummy_hash(self) -> PasswordHash:
        return _build_dummy_hash(*self._params)


def _build_hasher(time_cost: int, memory_cost: int, parallelism: int) -> Argon2Hasher:
    return Argon2Hasher(time_cost=time_cost, memory_cost=memory_cost, parallelism=parallelism)


@cache
def _build_dummy_hash(time_cost: int, memory_cost: int, parallelism: int) -> PasswordHash:
    # Una vez por proceso (el adaptador se instancia por request): cuesta lo
    # mismo que un hash real, y verificar contra él iguala el tiempo del login
    # con email inexistente al de uno con usuario real.
    hasher = _build_hasher(time_cost, memory_cost, parallelism)
    return PasswordHash(hasher.hash("Dummy-Timing-Hash-1!"))
