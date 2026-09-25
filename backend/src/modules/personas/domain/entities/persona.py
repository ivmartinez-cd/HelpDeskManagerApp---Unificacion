import re
import uuid
from dataclasses import dataclass
from datetime import datetime

from src.modules.personas.domain.errors import DatosPersonaInvalidosError

_PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PATRON_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def _normalizar_nombre(valor: str, campo: str) -> str:
    limpio = " ".join(valor.split())
    if not limpio:
        raise DatosPersonaInvalidosError(f"El {campo} no puede quedar vacío")
    return limpio


@dataclass(frozen=True, slots=True)
class DatosPersona:
    """Lo que la ficha y la cuenta comparten: se edita en un solo lugar y se
    escribe en los dos (unificación Personas, ADR-040)."""

    first_name: str
    last_name: str
    email: str
    color: str

    def __post_init__(self) -> None:
        email = self.email.strip().lower()
        if not _PATRON_EMAIL.match(email):
            raise DatosPersonaInvalidosError(f"Mail inválido: {self.email}")
        if not _PATRON_COLOR.match(self.color):
            raise DatosPersonaInvalidosError(f"Color inválido: {self.color}")
        object.__setattr__(self, "first_name", _normalizar_nombre(self.first_name, "nombre"))
        object.__setattr__(self, "last_name", _normalizar_nombre(self.last_name, "apellido"))
        object.__setattr__(self, "email", email)

    @property
    def nombre_completo(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass(frozen=True, slots=True)
class AccesoPersona:
    """Cuenta vinculada: existe solo si la persona entra (o entró) a la app."""

    user_id: uuid.UUID
    activo: bool
    superadmin: bool
    ultimo_ingreso: datetime | None


@dataclass(frozen=True, slots=True)
class Persona:
    """Lectura unificada: la ficha de empleado es la persona; el acceso es opcional.
    El `id` es el de la ficha."""

    id: uuid.UUID
    datos: DatosPersona
    activa: bool
    sector_id: uuid.UUID
    sector_nombre: str
    cargo_nombre: str
    acceso: AccesoPersona | None

    @property
    def entra_a_la_app(self) -> bool:
        return self.acceso is not None and self.acceso.activo
