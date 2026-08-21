from src.shared.domain.errors import (
    ApplicationError,
    BusinessRuleViolationError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


class InvalidEmailError(ValidationError):
    default_code = "INVALID_EMAIL"

    def __init__(self, raw_value: str) -> None:
        super().__init__(f"Email inválido: {raw_value!r}")


class WeakPasswordError(ValidationError):
    default_code = "WEAK_PASSWORD"


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


class TokenInvalidError(ApplicationError):
    http_status = 400
    default_code = "TOKEN_INVALID"

    def __init__(self) -> None:
        super().__init__("Token inválido")


class TokenExpiredError(ApplicationError):
    http_status = 400
    default_code = "TOKEN_EXPIRED"

    def __init__(self) -> None:
        super().__init__("Token vencido")


class TokenAlreadyUsedError(ApplicationError):
    http_status = 400
    default_code = "TOKEN_ALREADY_USED"

    def __init__(self) -> None:
        super().__init__("Este token ya fue usado")


class UserNotFoundError(NotFoundError):
    default_code = "USER_NOT_FOUND"

    def __init__(self) -> None:
        super().__init__("Usuario no encontrado")


class EmailAlreadyRegisteredError(BusinessRuleViolationError):
    default_code = "EMAIL_ALREADY_REGISTERED"

    def __init__(self) -> None:
        super().__init__("Ya existe un usuario con ese email")


class LastSuperadminError(BusinessRuleViolationError):
    default_code = "LAST_SUPERADMIN"

    def __init__(self) -> None:
        super().__init__("No podés desactivar al último superadmin activo")


class CannotDemoteSelfError(BusinessRuleViolationError):
    default_code = "CANNOT_DEMOTE_SELF"

    def __init__(self) -> None:
        super().__init__("No podés quitarte tu propio permiso de administración")


class InvalidRoutePathError(ValidationError):
    """Ver `RoutePath` (ADR-028) — la ruta no matchea la gramática de
    navegación esperada (esquema/query string/traversal/segmento inválido)."""

    default_code = "INVALID_ROUTE_PATH"

    def __init__(self, raw_value: str) -> None:
        super().__init__(f"Ruta inválida: {raw_value!r}")


class UnknownRouteError(ValidationError):
    """El primer segmento de la ruta no corresponde a ningún módulo
    habilitado del catálogo — el frontend solo debería postear su propia
    whitelist, así que esto es señal de un catálogo desincronizado."""

    default_code = "UNKNOWN_ROUTE"

    def __init__(self, raw_value: str) -> None:
        super().__init__(f"Ruta no reconocida: {raw_value!r}")


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
