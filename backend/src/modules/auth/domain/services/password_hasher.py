from typing import Protocol

from src.modules.auth.domain.value_objects.password_hash import PasswordHash
from src.modules.auth.domain.value_objects.raw_password import RawPassword


class PasswordHasher(Protocol):
    def hash(self, raw: RawPassword) -> PasswordHash: ...
    def verify(self, raw: RawPassword, stored: PasswordHash) -> bool: ...
    def needs_rehash(self, stored: PasswordHash) -> bool: ...
