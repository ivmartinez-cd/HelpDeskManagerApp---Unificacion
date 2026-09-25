import uuid
from typing import Protocol

from src.modules.personas.domain.entities.persona import DatosPersona


class CuentasGateway(Protocol):
    """Escritura sobre las cuentas de acceso a la app (auth)."""

    async def email_en_uso(self, email: str, *, excepto: uuid.UUID | None) -> bool: ...

    async def actualizar_datos(self, user_id: uuid.UUID, datos: DatosPersona) -> None: ...

    async def crear(self, datos: DatosPersona) -> uuid.UUID: ...

    async def activar(self, user_id: uuid.UUID) -> None: ...

    async def desactivar(self, user_id: uuid.UUID) -> None: ...


class AvisoActivacion(Protocol):
    """Manda a la persona el link para elegir su contraseña."""

    async def enviar(self, email: str) -> None: ...
