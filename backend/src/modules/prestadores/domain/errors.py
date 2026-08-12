from typing import ClassVar

from src.shared.domain.errors import NotFoundError


class PrestadorNotFoundError(NotFoundError):
    default_code: ClassVar[str] = "PRESTADOR_NOT_FOUND"

    def __init__(self) -> None:
        super().__init__("Prestador no encontrado")


class ContactoNotFoundError(NotFoundError):
    default_code: ClassVar[str] = "CONTACTO_NOT_FOUND"

    def __init__(self) -> None:
        super().__init__("Contacto no encontrado")
