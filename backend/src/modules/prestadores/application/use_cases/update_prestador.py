from dataclasses import dataclass

from src.modules.prestadores.application.dtos.prestador_dtos import (
    PrestadorDTO,
    UpdatePrestadorCommand,
)
from src.modules.prestadores.application.use_cases.prestador_dto_builder import (
    build_prestador_dto,
)
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.errors import PrestadorNotFoundError
from src.modules.prestadores.domain.repositories.contacto_repository import ContactoRepository
from src.modules.prestadores.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.prestadores.domain.repositories.user_provider import UserProvider


@dataclass(frozen=True, slots=True)
class UpdatePrestadorDependencies:
    prestadores: PrestadorRepository
    contactos: ContactoRepository
    users: UserProvider


class UpdatePrestador:
    """Caso de uso: edita los datos propios de un PST (no toca operador ni
    `is_active`, que tienen sus propios comandos)."""

    def __init__(self, deps: UpdatePrestadorDependencies) -> None:
        self._deps = deps

    async def execute(self, command: UpdatePrestadorCommand) -> PrestadorDTO:
        existing = await self._deps.prestadores.get_by_id(command.prestador_id)
        if existing is None:
            raise PrestadorNotFoundError()

        prestador = Prestador(
            id=existing.id,
            siges_empresa_id=existing.siges_empresa_id,
            den_comercial=command.den_comercial,
            razon_social=command.razon_social,
            cuit=command.cuit,
            equipos=existing.equipos,
            operador_id=existing.operador_id,
            is_active=existing.is_active,
        )
        await self._deps.prestadores.save(prestador)

        contactos = await self._deps.contactos.list_by_prestador(prestador.id)
        users = (
            await self._deps.users.get_users_by_ids([prestador.operador_id])
            if prestador.operador_id
            else {}
        )
        return build_prestador_dto(prestador, contactos, users)
