from typing import ClassVar

from src.shared.domain.errors import DomainError, NotFoundError


class LogParseError(DomainError):
    default_code: ClassVar[str] = "LOG_PARSE_ERROR"


class ErrorCodeNotFoundError(NotFoundError):
    default_code: ClassVar[str] = "ERROR_CODE_NOT_FOUND"

    def __init__(self, code: str) -> None:
        super().__init__(f"Código de error no encontrado: {code!r}")


class SavedAnalysisNotFoundError(NotFoundError):
    default_code: ClassVar[str] = "SAVED_ANALYSIS_NOT_FOUND"

    def __init__(self) -> None:
        super().__init__("Análisis guardado no encontrado")
