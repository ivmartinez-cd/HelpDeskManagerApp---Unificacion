from typing import ClassVar

from src.shared.domain.errors import BusinessRuleViolationError, NotFoundError, ValidationError


class PrestadorNotFoundError(NotFoundError):
    default_code: ClassVar[str] = "PRESTADOR_NOT_FOUND"

    def __init__(self) -> None:
        super().__init__("Prestador no encontrado")


class ContactoNotFoundError(NotFoundError):
    default_code: ClassVar[str] = "CONTACTO_NOT_FOUND"

    def __init__(self) -> None:
        super().__init__("Contacto no encontrado")


class AsignacionOverrideNotFoundError(NotFoundError):
    default_code: ClassVar[str] = "ASIGNACION_OVERRIDE_NOT_FOUND"

    def __init__(self) -> None:
        super().__init__("Override de asignación no encontrado")


class InvalidOverrideRangeError(ValidationError):
    default_code: ClassVar[str] = "INVALID_OVERRIDE_RANGE"

    def __init__(self) -> None:
        super().__init__("El rango de vigencia del override es inválido (desde > hasta)")


class OverrideMismoOperadorError(ValidationError):
    default_code: ClassVar[str] = "OVERRIDE_MISMO_OPERADOR"

    def __init__(self) -> None:
        super().__init__("El operador ausente y el reemplazante no pueden ser el mismo")


class OverrideNoEditableError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "OVERRIDE_NO_EDITABLE"

    def __init__(self) -> None:
        super().__init__(
            "Solo se puede editar un override activo — uno cancelado es un registro histórico"
        )


class OverlappingOverrideError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "OVERLAPPING_OVERRIDE"

    def __init__(self) -> None:
        super().__init__(
            "Ya existe un override activo para ese operador ausente con fechas superpuestas "
            "y alcance en común"
        )
