import re
from dataclasses import dataclass

from src.modules.auth.domain.errors import WeakPasswordError

_MIN_LENGTH = 8
# Tope para que un body hostil no gaste CPU de argon2 (los schemas HTTP lo
# repiten con max_length; acá es la fuente de verdad).
MAX_PASSWORD_LENGTH = 128
_UPPERCASE = re.compile(r"[A-Z]")
_DIGIT = re.compile(r"[0-9]")
_SPECIAL = re.compile(r"[^A-Za-z0-9]")


@dataclass(frozen=True, slots=True)
class RawPassword:
    """Password en texto plano, solo vive en memoria durante login/registro.

    Política: los mismos 4 checks que VacaSync (≥8, mayúscula, número,
    especial) — ver riesgo #11 del plan de auth si se quiere endurecer.
    """

    value: str

    def __post_init__(self) -> None:
        if len(self.value) < _MIN_LENGTH:
            raise WeakPasswordError("Debe tener al menos 8 caracteres")
        if len(self.value) > MAX_PASSWORD_LENGTH:
            raise WeakPasswordError(f"No puede superar {MAX_PASSWORD_LENGTH} caracteres")
        if not _UPPERCASE.search(self.value):
            raise WeakPasswordError("Debe contener al menos una mayúscula")
        if not _DIGIT.search(self.value):
            raise WeakPasswordError("Debe contener al menos un número")
        if not _SPECIAL.search(self.value):
            raise WeakPasswordError("Debe contener al menos un carácter especial")
