from typing import Protocol

from src.modules.auth.domain.value_objects.password_hash import PasswordHash
from src.modules.auth.domain.value_objects.raw_password import RawPassword


class PasswordHasher(Protocol):
    """`verify` toma un `str` crudo, no un `RawPassword`: verificar un login
    no debe aplicar la política de fuerza vigente — un hash guardado pudo
    corresponder a una política anterior, o el usuario simplemente tipeó
    mal, y en ningún caso corresponde ahí un error de "password débil"."""

    def hash(self, raw: RawPassword) -> PasswordHash: ...
    def verify(self, candidate: str, stored: PasswordHash) -> bool: ...
    def needs_rehash(self, stored: PasswordHash) -> bool: ...
