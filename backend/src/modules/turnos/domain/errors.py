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


# --- Grilla variante (modo vacaciones, ADR-025) ---------------------------------


class GrillaVarianteNotFoundError(NotFoundError):
    default_code: ClassVar[str] = "GRILLA_VARIANTE_NOT_FOUND"

    def __init__(self) -> None:
        super().__init__("Grilla de vacaciones no encontrada")


class InvalidVarianteRangeError(ValidationError):
    default_code: ClassVar[str] = "INVALID_VARIANTE_RANGE"

    def __init__(self) -> None:
        super().__init__("El rango de vigencia de la grilla es inválido (desde > hasta)")


class VarianteSinFranjasError(ValidationError):
    default_code: ClassVar[str] = "VARIANTE_SIN_FRANJAS"

    def __init__(self) -> None:
        super().__init__(
            "La grilla de vacaciones necesita al menos una franja -- vacía, dejaría todas las "
            "casillas sin cobertura durante la vigencia"
        )


class VarianteCasillaInvalidaError(ValidationError):
    default_code: ClassVar[str] = "VARIANTE_CASILLA_INVALIDA"

    def __init__(self) -> None:
        super().__init__("Una franja de la grilla referencia una casilla inexistente")


class VarianteFranjaInvalidaError(ValidationError):
    default_code: ClassVar[str] = "VARIANTE_FRANJA_INVALIDA"

    def __init__(self, detalle: str) -> None:
        super().__init__(f"Franja inválida: {detalle}")


class VarianteFranjasSolapadasError(ValidationError):
    default_code: ClassVar[str] = "VARIANTE_FRANJAS_SOLAPADAS"

    def __init__(self, detalle: str) -> None:
        super().__init__(f"Dos franjas de la misma casilla y día se superponen: {detalle}")


class VarianteOperadorSolapadoError(ValidationError):
    default_code: ClassVar[str] = "VARIANTE_OPERADOR_SOLAPADO"

    def __init__(self, detalle: str) -> None:
        super().__init__(
            f"Un mismo operador está asignado a dos franjas que se superponen: {detalle}"
        )


class VarianteNoEditableError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "VARIANTE_NO_EDITABLE"

    def __init__(self) -> None:
        super().__init__(
            "Solo se puede editar una grilla de vacaciones activa -- una cancelada es un "
            "registro histórico"
        )


class OverlappingVarianteError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "OVERLAPPING_VARIANTE"

    def __init__(self) -> None:
        super().__init__(
            "Ya existe una grilla de vacaciones activa con fechas superpuestas -- solo puede "
            "haber una vigente por fecha"
        )
