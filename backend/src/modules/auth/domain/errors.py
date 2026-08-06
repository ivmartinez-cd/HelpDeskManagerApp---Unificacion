from src.shared.domain.errors import ApplicationError, UnauthorizedError, ValidationError


class InvalidEmailError(ValidationError):
    default_code = "INVALID_EMAIL"

    def __init__(self, raw_value: str) -> None:
        super().__init__(f"Email inválido: {raw_value!r}")


class WeakPasswordError(ValidationError):
    default_code = "WEAK_PASSWORD"


class InvalidModuleKeyError(ValidationError):
    default_code = "INVALID_MODULE_KEY"

    def __init__(self, raw_value: str) -> None:
        super().__init__(f"Clave de módulo inválida: {raw_value!r}")


class InvalidActionKeyError(ValidationError):
    default_code = "INVALID_ACTION_KEY"

    def __init__(self, raw_value: str) -> None:
        super().__init__(f"Clave de acción inválida: {raw_value!r}")


class InvalidCredentialsError(UnauthorizedError):
    """Mismo error para email inexistente y password incorrecto — no hay
    forma de distinguirlos desde afuera (anti-enumeración)."""

    default_code = "INVALID_CREDENTIALS"

    def __init__(self) -> None:
        super().__init__("Credenciales inválidas")


class NotAuthenticatedError(UnauthorizedError):
    default_code = "NOT_AUTHENTICATED"

    def __init__(self) -> None:
        super().__init__("No autenticado")


class AccountDisabledError(ApplicationError):
    http_status = 403
    default_code = "ACCOUNT_DISABLED"

    def __init__(self) -> None:
        super().__init__("La cuenta está deshabilitada")


class TooManyAttemptsError(ApplicationError):
    http_status = 429
    default_code = "TOO_MANY_ATTEMPTS"

    def __init__(self, *, retry_after_seconds: int) -> None:
        super().__init__(
            "Demasiados intentos, esperá antes de volver a intentar",
            headers={"Retry-After": str(retry_after_seconds)},
        )
