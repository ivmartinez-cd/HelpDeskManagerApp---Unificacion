import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.prestadores.application.dtos.prestador_dtos import (
    CreatePrestadorCommand,
    PrestadorDTO,
)
from src.modules.prestadores.application.use_cases.prestador_dto_builder import (
    build_prestador_dto,
)
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.repositories.asignacion_historial_repository import (
    AsignacionHistorialRepository,
)
from src.modules.prestadores.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.prestadores.domain.repositories.user_provider import UserProvider


@dataclass(frozen=True, slots=True)
class CreatePrestadorDependencies:
    prestadores: PrestadorRepository
    asignaciones: AsignacionHistorialRepository
    users: UserProvider


class CreatePrestador:
    """Caso de uso: alta manual de un PST. Si viene con operador ya asignado,
    abre también el primer tramo de historial."""

    def __init__(self, deps: CreatePrestadorDependencies) -> None:
        self._deps = deps

    async def execute(self, command: CreatePrestadorCommand) -> PrestadorDTO:
        prestador = Prestador(
            id=uuid.uuid4(),
            siges_empresa_id=command.siges_empresa_id,
            den_comercial=command.den_comercial,
            razon_social=command.razon_social,
            cuit=command.cuit,
            equipos=command.equipos,
            operador_id=command.operador_id,
            is_active=True,
        )
        await self._deps.prestadores.add(prestador)
        if command.operador_id is not None:
            await self._deps.asignaciones.reasignar(
                prestador.id, command.operador_id, datetime.now(UTC).date()
            )
        users = (
            await self._deps.users.get_users_by_ids([command.operador_id])
            if command.operador_id
            else {}
        )
        return build_prestador_dto(prestador, [], users)
