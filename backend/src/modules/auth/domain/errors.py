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


class ForbiddenError(ApplicationError):
    """Fail-closed: la ausencia de grant o un módulo deshabilitado dan este
    mismo error. `is_superadmin` evita el chequeo de grant (bootstrap: el
    primer superadmin no tiene una sola fila en permission_grant y aun así
    necesita poder entrar a /admin para cargar la matriz de todos los
    demás), pero NO evita el chequeo de is_enabled — ese es un gate de
    despliegue ("¿este módulo ya está migrado?"), no de delegación."""

    http_status = 403
    default_code = "FORBIDDEN"

    def __init__(self) -> None:
        super().__init__("No tenés permiso para esta acción")
