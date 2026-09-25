from typing import ClassVar

from src.shared.domain.errors import NotFoundError, ValidationError


class PeriodoInvalidoError(ValidationError):
    default_code: ClassVar[str] = "PERIODO_INVALIDO"

    def __init__(self, raw_value: str) -> None:
        super().__init__(f"Período inválido (se espera AAAA-MM): {raw_value!r}")


class EmpresaNoEncontradaError(NotFoundError):
    default_code: ClassVar[str] = "EMPRESA_NO_ENCONTRADA"

    def __init__(self, empresa_id: str) -> None:
        super().__init__(f"No existe un cliente activo con id {empresa_id!r}")
