import uuid
from typing import ClassVar

from src.shared.domain.errors import (
    ApplicationError,
    BusinessRuleViolationError,
    NotFoundError,
    ValidationError,
)


class PersonaNoEncontradaError(NotFoundError):
    default_code = "PERSONA_NOT_FOUND"

    def __init__(self, persona_id: uuid.UUID) -> None:
        super().__init__(f"No existe la persona {persona_id}")


class DatosPersonaInvalidosError(ValidationError):
    default_code = "PERSONA_DATOS_INVALIDOS"


class EmailEnUsoError(BusinessRuleViolationError):
    default_code = "PERSONA_EMAIL_EN_USO"

    def __init__(self, email: str) -> None:
        super().__init__(f"El mail {email} ya lo usa otra persona o cuenta")


class PersonaInactivaError(BusinessRuleViolationError):
    default_code = "PERSONA_INACTIVA"

    def __init__(self) -> None:
        super().__init__("No se puede dar acceso a la app a una persona inactiva")


class CambioDeMailNoPermitidoError(ApplicationError):
    """Cambiar el mail de quien entra a la app cambia su login: exige el permiso
    de gestionar accesos, no solo el de editar datos."""

    http_status: ClassVar[int] = 403
    default_code = "PERSONA_CAMBIO_MAIL_NO_PERMITIDO"

    def __init__(self) -> None:
        super().__init__(
            "Cambiar el mail de alguien que entra a la app requiere el permiso de gestionar accesos"
        )


class CuentaPrivilegiadaError(ApplicationError):
    """El mail y el acceso de un superadmin o de quien administra permisos solo los
    toca un superadmin: cambiarle el mail y pedir el reseteo de contraseña sería
    quedarse con su cuenta."""

    http_status: ClassVar[int] = 403
    default_code = "PERSONA_CUENTA_PRIVILEGIADA"

    def __init__(self) -> None:
        super().__init__(
            "El mail y el acceso de un administrador solo los puede cambiar un superadmin"
        )
