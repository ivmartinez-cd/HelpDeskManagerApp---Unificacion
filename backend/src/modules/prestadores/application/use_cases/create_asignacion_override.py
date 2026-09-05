import uuid
from dataclasses import dataclass
from typing import Literal

from src.modules.prestadores.application.dtos.prestador_dtos import (
    AsignacionOverrideDTO,
    CreateAsignacionOverrideCommand,
)
from src.modules.prestadores.application.use_cases._referencias import (
    exigir_operadores,
    exigir_prestadores,
)
from src.modules.prestadores.application.use_cases.asignacion_override_dto_builder import (
    build_asignacion_override_dto,
)
from src.modules.prestadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.prestadores.domain.errors import (
    InvalidOverrideRangeError,
    OverlappingOverrideError,
    OverrideMismoOperadorError,
)
from src.modules.prestadores.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
)
from src.modules.prestadores.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.prestadores.domain.repositories.user_provider import UserProvider
from src.shared.domain.services.asignacion_override_resolver import hay_solapamiento


@dataclass(frozen=True, slots=True)
class CreateAsignacionOverrideDependencies:
    overrides: AsignacionOverrideRepository
    users: UserProvider
    prestadores: PrestadorRepository


class CreateAsignacionOverride:
    """Caso de uso: da de alta un override temporal de asignación (ver
    ADR-013). No toca `Prestador.operador_id` ni `AsignacionHistorial`."""

    def __init__(self, deps: CreateAsignacionOverrideDependencies) -> None:
        self._deps = deps

    async def execute(self, command: CreateAsignacionOverrideCommand) -> AsignacionOverrideDTO:
        if command.desde > command.hasta:
            raise InvalidOverrideRangeError()
        if command.operador_ausente_id == command.operador_reemplazante_id:
            raise OverrideMismoOperadorError()
        users = await exigir_operadores(
            self._deps.users, [command.operador_ausente_id, command.operador_reemplazante_id]
        )
        await exigir_prestadores(self._deps.prestadores, command.prestador_ids or [])

        alcance: Literal["TOTAL"] | frozenset[uuid.UUID] = (
            "TOTAL" if command.prestador_ids is None else frozenset(command.prestador_ids)
        )
        existentes = await self._deps.overrides.list_activos_por_ausente(
            command.operador_ausente_id
        )
        if hay_solapamiento(command.desde, command.hasta, alcance, existentes):
            raise OverlappingOverrideError()

        override = AsignacionOverride(
            id=uuid.uuid4(),
            operador_ausente_id=command.operador_ausente_id,
            operador_reemplazante_id=command.operador_reemplazante_id,
            desde=command.desde,
            hasta=command.hasta,
            alcance=alcance,
            estado="ACTIVA",
            motivo=command.motivo,
            created_by_user_id=command.created_by_user_id,
        )
        await self._deps.overrides.create(override)
        return build_asignacion_override_dto(override, users)
