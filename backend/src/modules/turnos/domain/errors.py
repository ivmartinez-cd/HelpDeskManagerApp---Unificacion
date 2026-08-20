from typing import ClassVar

from src.shared.domain.errors import BusinessRuleViolationError, NotFoundError, ValidationError


class AsignacionOverrideNotFoundError(NotFoundError):
    default_code: ClassVar[str] = "ASIGNACION_OVERRIDE_NOT_FOUND"

    def __init__(self) -> None:
        super().__init__("Cobertura de turnos no encontrada")


class InvalidOverrideRangeError(ValidationError):
    default_code: ClassVar[str] = "INVALID_OVERRIDE_RANGE"

    def __init__(self) -> None:
        super().__init__("El rango de vigencia de la cobertura es inválido (desde > hasta)")


class OverrideMismoOperadorError(ValidationError):
    default_code: ClassVar[str] = "OVERRIDE_MISMO_OPERADOR"

    def __init__(self) -> None:
        super().__init__("El operador ausente y el reemplazante no pueden ser el mismo")


class OverrideNoEditableError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "OVERRIDE_NO_EDITABLE"

    def __init__(self) -> None:
        super().__init__(
            "Solo se puede editar una cobertura activa -- una cancelada es un registro histórico"
        )


class OverlappingOverrideError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "OVERLAPPING_OVERRIDE"

    def __init__(self) -> None:
        super().__init__(
            "Ya existe una cobertura activa para ese operador ausente con fechas superpuestas "
            "y franjas en común"
        )
