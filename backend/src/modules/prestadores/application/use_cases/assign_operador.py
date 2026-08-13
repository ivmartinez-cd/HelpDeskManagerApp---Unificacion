from dataclasses import dataclass

from src.modules.prestadores.application.dtos.prestador_dtos import (
    AssignOperadorCommand,
    PrestadorDTO,
)
from src.modules.prestadores.application.use_cases.prestador_dto_builder import (
    build_prestador_dto,
)
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.errors import PrestadorNotFoundError
from src.modules.prestadores.domain.repositories.asignacion_historial_repository import (
    AsignacionHistorialRepository,
)
from src.modules.prestadores.domain.repositories.contacto_repository import ContactoRepository
from src.modules.prestadores.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.prestadores.domain.repositories.user_provider import UserProvider


@dataclass(frozen=True, slots=True)
class AssignOperadorDependencies:
    prestadores: PrestadorRepository
    asignaciones: AsignacionHistorialRepository
    contactos: ContactoRepository
    users: UserProvider


class AssignOperador:
    """Caso de uso: reasigna (o desasigna, con `operador_id=None`) el operador
    de un PST. Actualiza el puntero rápido en `Prestador.operador_id` y cierra
    el tramo de historial vigente para abrir uno nuevo."""

    def __init__(self, deps: AssignOperadorDependencies) -> None:
        self._deps = deps

    async def execute(self, command: AssignOperadorCommand) -> PrestadorDTO:
        existing = await self._deps.prestadores.get_by_id(command.prestador_id)
        if existing is None:
            raise PrestadorNotFoundError()

        prestador = Prestador(
            id=existing.id,
            siges_empresa_id=existing.siges_empresa_id,
            den_comercial=existing.den_comercial,
            razon_social=existing.razon_social,
            cuit=existing.cuit,
            equipos=existing.equipos,
            operador_id=command.operador_id,
            is_active=existing.is_active,
        )
        await self._deps.prestadores.save(prestador)
        await self._deps.asignaciones.reasignar(
            prestador.id, command.operador_id, command.desde
        )

        contactos = await self._deps.contactos.list_by_prestador(prestador.id)
        users = (
            await self._deps.users.get_users_by_ids([command.operador_id])
            if command.operador_id
            else {}
        )
        return build_prestador_dto(prestador, contactos, users)
