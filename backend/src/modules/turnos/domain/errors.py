from collections.abc import Iterable
from typing import ClassVar

from src.shared.domain.errors import BusinessRuleViolationError, NotFoundError, ValidationError


class CasillaNotFoundError(NotFoundError):
    default_code: ClassVar[str] = "CASILLA_NOT_FOUND"

    def __init__(self, casilla_id: object) -> None:
        super().__init__(f"Casilla {casilla_id} no existe")


class CasillaNombreVacioError(ValidationError):
    default_code: ClassVar[str] = "CASILLA_NOMBRE_VACIO"

    def __init__(self) -> None:
        super().__init__("El nombre de la casilla no puede estar vacío")


class CasillaNombreDuplicadoError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "CASILLA_NOMBRE_DUPLICADO"

    def __init__(self, nombre: str) -> None:
        super().__init__(f"Ya existe una casilla con el nombre {nombre!r}")


class CasillaEnUsoError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "CASILLA_EN_USO"

    def __init__(self, detalle: str) -> None:
        super().__init__(f"La casilla no se puede borrar: {detalle}")


class SlotNotFoundError(NotFoundError):
    default_code: ClassVar[str] = "SLOT_NOT_FOUND"

    def __init__(self, slot_id: object) -> None:
        super().__init__(f"Franja {slot_id} no existe")


class FranjaInvalidaError(ValidationError):
    default_code: ClassVar[str] = "FRANJA_INVALIDA"

    def __init__(self, detalle: str) -> None:
        super().__init__(f"Franja inválida: {detalle}")


class FranjasSolapadasError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "FRANJAS_SOLAPADAS"

    def __init__(self, detalle: str) -> None:
        super().__init__(f"La franja se superpone con otra de la misma casilla y día: {detalle}")


class SlotEnUsoError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "SLOT_EN_USO"

    def __init__(self, detalle: str) -> None:
        super().__init__(f"La franja no se puede borrar: {detalle}")


class UsuarioNotFoundError(NotFoundError):
    """Usuario referenciado por una asignación/cobertura/grilla que no existe
    en `app_user`. Antes llegaba como `IntegrityError` (500)."""

    default_code: ClassVar[str] = "USUARIO_NOT_FOUND"

    def __init__(self, user_ids: Iterable[object]) -> None:
        ids = ", ".join(sorted(str(u) for u in user_ids))
        super().__init__(f"Usuario(s) inexistente(s): {ids}")


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


# --- Intercambio de turnos (ADR-026) ----------------------------------------------


class IntercambioNotFoundError(NotFoundError):
    default_code: ClassVar[str] = "INTERCAMBIO_NOT_FOUND"

    def __init__(self) -> None:
        super().__init__("Intercambio de turnos no encontrado")


class OverrideEsIntercambioError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "OVERRIDE_ES_INTERCAMBIO"

    def __init__(self) -> None:
        super().__init__(
            "Esta cobertura forma parte de un intercambio -- se edita por el intercambio, "
            "nunca una mitad sola"
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
