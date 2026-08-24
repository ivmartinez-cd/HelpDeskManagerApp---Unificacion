from typing import ClassVar

from src.shared.domain.errors import ValidationError


class PeriodoInvalidoError(ValidationError):
    default_code: ClassVar[str] = "PERIODO_INVALIDO"

    def __init__(self, raw_value: int) -> None:
        super().__init__(f"Período inválido (se espera AAAAMM): {raw_value!r}")


class ValorInvalidoError(ValidationError):
    """Días/Tareas Varias (carga manual, celdas `Lista!$J$6`/`$J$7` del Excel)
    no pueden ser negativos."""

    default_code: ClassVar[str] = "VALOR_INVALIDO"

    def __init__(self, campo: str, raw_value: int) -> None:
        super().__init__(f"{campo} inválido (no puede ser negativo): {raw_value!r}")
