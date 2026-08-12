import uuid
from dataclasses import dataclass

from src.modules.prestadores.domain.errors import ContactoNotFoundError
from src.modules.prestadores.domain.repositories.contacto_repository import ContactoRepository


@dataclass(frozen=True, slots=True)
class DeleteContactoDependencies:
    contactos: ContactoRepository


class DeleteContacto:
    def __init__(self, deps: DeleteContactoDependencies) -> None:
        self._deps = deps

    async def execute(self, contacto_id: uuid.UUID) -> None:
        existing = await self._deps.contactos.get_by_id(contacto_id)
        if existing is None:
            raise ContactoNotFoundError()
        await self._deps.contactos.delete(contacto_id)
