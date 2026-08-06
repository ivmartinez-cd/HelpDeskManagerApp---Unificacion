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
        self._hasher = Argon2Hasher(
            time_cost=settings.argon2_time_cost,
            memory_cost=settings.argon2_memory_cost_kib,
            parallelism=settings.argon2_parallelism,
        )

    def hash(self, raw: RawPassword) -> PasswordHash:
        return PasswordHash(self._hasher.hash(raw.value))

    def verify(self, raw: RawPassword, stored: PasswordHash) -> bool:
        try:
            return self._hasher.verify(stored.value, raw.value)
        except VerifyMismatchError:
            return False

    def needs_rehash(self, stored: PasswordHash) -> bool:
        return self._hasher.check_needs_rehash(stored.value)
