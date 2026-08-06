import re
from dataclasses import dataclass

from src.modules.auth.domain.errors import WeakPasswordError

_MIN_LENGTH = 8
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
        if not _UPPERCASE.search(self.value):
            raise WeakPasswordError("Debe contener al menos una mayúscula")
        if not _DIGIT.search(self.value):
            raise WeakPasswordError("Debe contener al menos un número")
        if not _SPECIAL.search(self.value):
            raise WeakPasswordError("Debe contener al menos un carácter especial")
