import uuid
from typing import Protocol

from src.modules.personas.domain.entities.persona import DatosPersona


class FichasGateway(Protocol):
    """Escritura sobre la ficha de empleado (Gestión de Personal)."""

    async def email_en_uso(self, email: str, *, excepto: uuid.UUID) -> bool: ...

    async def actualizar_datos(self, persona_id: uuid.UUID, datos: DatosPersona) -> None: ...

    async def vincular_cuenta(self, persona_id: uuid.UUID, user_id: uuid.UUID) -> None: ...
