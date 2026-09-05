from dataclasses import dataclass
from datetime import date

from src.modules.prestadores.application.dtos.prestador_dtos import (
    AssignOperadorCommand,
    PrestadorDTO,
)
from src.modules.prestadores.application.use_cases._referencias import exigir_operadores
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
    de un PST desde una fecha. Escribe el historial y mantiene el puntero
    rápido `Prestador.operador_id` como "operador vigente HOY": una
    asignación con `desde` futura queda programada en el historial (el
    listado y el detalle la resuelven por fecha) sin adelantar el puntero."""

    def __init__(self, deps: AssignOperadorDependencies) -> None:
        self._deps = deps

    async def execute(self, command: AssignOperadorCommand) -> PrestadorDTO:
        existing = await self._deps.prestadores.get_by_id(command.prestador_id)
        if existing is None:
            raise PrestadorNotFoundError()
        users = await exigir_operadores(self._deps.users, [command.operador_id])

        vigente_hoy = command.desde <= date.today()
        prestador = Prestador(
            id=existing.id,
            siges_empresa_id=existing.siges_empresa_id,
            den_comercial=existing.den_comercial,
            razon_social=existing.razon_social,
            cuit=existing.cuit,
            equipos=existing.equipos,
            operador_id=command.operador_id if vigente_hoy else existing.operador_id,
            is_active=existing.is_active,
        )
        await self._deps.prestadores.save(prestador)
        await self._deps.asignaciones.reasignar(prestador.id, command.operador_id, command.desde)

        contactos = await self._deps.contactos.list_by_prestador(prestador.id)
        if not vigente_hoy and prestador.operador_id is not None:
            users = await self._deps.users.get_users_by_ids([prestador.operador_id])
        return build_prestador_dto(prestador, contactos, users)
