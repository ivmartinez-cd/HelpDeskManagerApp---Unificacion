import uuid
from dataclasses import dataclass

from src.modules.prestadores.application.dtos.prestador_dtos import (
    ContactoDTO,
    UpsertContactoCommand,
)
from src.modules.prestadores.domain.entities.contacto_prestador import ContactoPrestador
from src.modules.prestadores.domain.errors import ContactoNotFoundError
from src.modules.prestadores.domain.repositories.contacto_repository import ContactoRepository


@dataclass(frozen=True, slots=True)
class UpsertContactoDependencies:
    contactos: ContactoRepository


class UpsertContacto:
    """Caso de uso: crea o edita un contacto de PST. Un PST puede tener varios
    (ej. San Juan tiene 3 en la planilla real)."""

    def __init__(self, deps: UpsertContactoDependencies) -> None:
        self._deps = deps

    async def execute(self, command: UpsertContactoCommand) -> ContactoDTO:
        if command.contacto_id is None:
            contacto = ContactoPrestador(
                id=uuid.uuid4(),
                prestador_id=command.prestador_id,
                nombre=command.nombre,
                telefono=command.telefono,
                email=command.email,
                is_principal=command.is_principal,
                sort_order=command.sort_order,
            )
            await self._deps.contactos.add(contacto)
        else:
            existing = await self._deps.contactos.get_by_id(command.contacto_id)
            if existing is None:
                raise ContactoNotFoundError()
            contacto = ContactoPrestador(
                id=existing.id,
                prestador_id=existing.prestador_id,
                nombre=command.nombre,
                telefono=command.telefono,
                email=command.email,
                is_principal=command.is_principal,
                sort_order=command.sort_order,
            )
            await self._deps.contactos.save(contacto)

        return ContactoDTO(
            id=contacto.id,
            prestador_id=contacto.prestador_id,
            nombre=contacto.nombre,
            telefono=contacto.telefono,
            email=contacto.email,
            is_principal=contacto.is_principal,
            sort_order=contacto.sort_order,
        )
