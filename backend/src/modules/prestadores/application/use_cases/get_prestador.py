import uuid
from dataclasses import dataclass

from src.modules.prestadores.application.dtos.prestador_dtos import PrestadorDTO
from src.modules.prestadores.application.use_cases.prestador_dto_builder import (
    build_prestador_dto,
)
from src.modules.prestadores.domain.errors import PrestadorNotFoundError
from src.modules.prestadores.domain.repositories.contacto_repository import ContactoRepository
from src.modules.prestadores.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.prestadores.domain.repositories.user_provider import UserProvider


@dataclass(frozen=True, slots=True)
class GetPrestadorDependencies:
    prestadores: PrestadorRepository
    contactos: ContactoRepository
    users: UserProvider


class GetPrestador:
    """Caso de uso: detalle de un PST con sus contactos y operador."""

    def __init__(self, deps: GetPrestadorDependencies) -> None:
        self._deps = deps

    async def execute(self, prestador_id: uuid.UUID) -> PrestadorDTO:
        prestador = await self._deps.prestadores.get_by_id(prestador_id)
        if prestador is None:
            raise PrestadorNotFoundError()
        contactos = await self._deps.contactos.list_by_prestador(prestador_id)
        users = (
            await self._deps.users.get_users_by_ids([prestador.operador_id])
            if prestador.operador_id
            else {}
        )
        return build_prestador_dto(prestador, contactos, users)
