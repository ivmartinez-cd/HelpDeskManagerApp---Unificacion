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
    (ej. San Juan tiene 3 en la planilla real), pero a lo sumo uno principal:
    marcar uno desmarca al anterior."""

    def __init__(self, deps: UpsertContactoDependencies) -> None:
        self._deps = deps

    async def execute(self, command: UpsertContactoCommand) -> ContactoDTO:
        if command.contacto_id is None:
            contacto = _nuevo(command, uuid.uuid4(), command.prestador_id)
            await self._deps.contactos.add(contacto)
        else:
            existing = await self._deps.contactos.get_by_id(command.contacto_id)
            if existing is None:
                raise ContactoNotFoundError()
            contacto = _nuevo(command, existing.id, existing.prestador_id)
            await self._deps.contactos.save(contacto)

        if contacto.is_principal:
            await self._desmarcar_otros_principales(contacto)
        return _to_dto(contacto)

    async def _desmarcar_otros_principales(self, principal: ContactoPrestador) -> None:
        for otro in await self._deps.contactos.list_by_prestador(principal.prestador_id):
            if otro.id != principal.id and otro.is_principal:
                otro.is_principal = False
                await self._deps.contactos.save(otro)


def _nuevo(
    command: UpsertContactoCommand, contacto_id: uuid.UUID, prestador_id: uuid.UUID
) -> ContactoPrestador:
    return ContactoPrestador(
        id=contacto_id,
        prestador_id=prestador_id,
        nombre=command.nombre,
        telefono=command.telefono,
        email=command.email,
        is_principal=command.is_principal,
        sort_order=command.sort_order,
    )


def _to_dto(contacto: ContactoPrestador) -> ContactoDTO:
    return ContactoDTO(
        id=contacto.id,
        prestador_id=contacto.prestador_id,
        nombre=contacto.nombre,
        telefono=contacto.telefono,
        email=contacto.email,
        is_principal=contacto.is_principal,
        sort_order=contacto.sort_order,
    )
