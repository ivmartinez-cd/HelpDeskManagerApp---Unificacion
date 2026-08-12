import uuid
from dataclasses import dataclass


@dataclass(slots=True, eq=False)
class ContactoPrestador:
    """Un contacto de un PST. Un PST puede tener varios (ej. varias sucursales
    de la misma razón social, cada una con su persona de contacto)."""

    id: uuid.UUID
    prestador_id: uuid.UUID
    nombre: str
    telefono: str | None
    email: str | None
    is_principal: bool
    sort_order: int

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ContactoPrestador) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
