from src.shared.domain.errors import ValidationError


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
