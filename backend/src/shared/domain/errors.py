from typing import ClassVar


class AppError(Exception):
    """Base de la jerarquía de errores (ARCHITECTURE_GUIDE.md §6)."""

    http_status: ClassVar[int] = 500
    default_code: ClassVar[str] = "INTERNAL_ERROR"

    def __init__(
        self, message: str, *, code: str | None = None, details: object | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.details = details


class DomainError(AppError):
    http_status: ClassVar[int] = 400
    default_code: ClassVar[str] = "DOMAIN_ERROR"


class ValidationError(DomainError):
    http_status: ClassVar[int] = 400
    default_code: ClassVar[str] = "VALIDATION_ERROR"


class BusinessRuleViolationError(DomainError):
    http_status: ClassVar[int] = 409
    default_code: ClassVar[str] = "BUSINESS_RULE_VIOLATION"


class ApplicationError(AppError):
    http_status: ClassVar[int] = 400
    default_code: ClassVar[str] = "APPLICATION_ERROR"


class NotFoundError(ApplicationError):
    http_status: ClassVar[int] = 404
    default_code: ClassVar[str] = "NOT_FOUND"


class UnauthorizedError(ApplicationError):
    http_status: ClassVar[int] = 401
    default_code: ClassVar[str] = "NOT_AUTHENTICATED"


class InfrastructureError(AppError):
    http_status: ClassVar[int] = 500
    default_code: ClassVar[str] = "INFRASTRUCTURE_ERROR"


class DatabaseError(InfrastructureError):
    http_status: ClassVar[int] = 500
    default_code: ClassVar[str] = "DATABASE_ERROR"


class ExternalServiceError(InfrastructureError):
    http_status: ClassVar[int] = 502
    default_code: ClassVar[str] = "EXTERNAL_SERVICE_ERROR"
