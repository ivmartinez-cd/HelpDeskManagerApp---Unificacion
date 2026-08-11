from typing import ClassVar

from src.shared.domain.errors import ValidationError


class PeriodoInvalidoError(ValidationError):
    default_code: ClassVar[str] = "PERIODO_INVALIDO"

    def __init__(self, raw_value: int) -> None:
        super().__init__(f"Período inválido (se espera AAAAMM): {raw_value!r}")
