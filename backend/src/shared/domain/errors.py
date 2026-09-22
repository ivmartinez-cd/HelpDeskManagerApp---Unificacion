from typing import ClassVar


class AppError(Exception):
    """Base de la jerarquía de errores (ARCHITECTURE_GUIDE.md §6)."""

    http_status: ClassVar[int] = 500
    default_code: ClassVar[str] = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: object | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.details = details
        self.headers = headers


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


class ExternalPermissionDeniedError(ExternalServiceError):
    """El servicio externo aceptó la identidad de la app pero su ACL no la habilita
    para esa operación (ej. wsAyC 403). No es un 403 de la app: queda en 502 para que
    el frontend no lo confunda con un permiso propio del usuario logueado."""

    default_code: ClassVar[str] = "EXTERNAL_PERMISSION_DENIED"
    user_message: ClassVar[str] = (
        "No tenés permisos para realizar esta acción. Avisale al administrador."
    )


class InvalidModuleKeyError(ValidationError):
    """`ModuleKey`/`ActionKey` viven en shared (ver ADR-007): todo módulo de
    negocio los usa para declarar sus propios permisos, no son de auth."""

    default_code: ClassVar[str] = "INVALID_MODULE_KEY"

    def __init__(self, raw_value: str) -> None:
        super().__init__(f"Clave de módulo inválida: {raw_value!r}")


class InvalidActionKeyError(ValidationError):
    default_code: ClassVar[str] = "INVALID_ACTION_KEY"

    def __init__(self, raw_value: str) -> None:
        super().__init__(f"Clave de acción inválida: {raw_value!r}")
