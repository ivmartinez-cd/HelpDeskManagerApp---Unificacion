import uuid
from dataclasses import dataclass
from typing import Literal

from src.modules.turnos.application.dtos.turno_dtos import (
    AsignacionOverrideDTO,
    CreateAsignacionOverrideCommand,
)
from src.modules.turnos.application.use_cases.asignacion_override_dto_builder import (
    build_asignacion_override_dto,
)
from src.modules.turnos.application.use_cases.usuarios_support import validar_usuarios_existen
from src.modules.turnos.domain.errors import (
    InvalidOverrideRangeError,
    OverlappingOverrideError,
    OverrideMismoOperadorError,
)
from src.modules.turnos.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
    TurnoAsignacionOverride,
)
from src.modules.turnos.domain.repositories.user_provider import UserProvider
from src.shared.domain.services.asignacion_override_resolver import hay_solapamiento
from src.shared.domain.value_objects.asignacion_override import AsignacionOverride


@dataclass(frozen=True, slots=True)
class CreateAsignacionOverrideDependencies:
    overrides: AsignacionOverrideRepository
    users: UserProvider


class CreateAsignacionOverride:
    """Caso de uso: da de alta una cobertura temporal de turnos (ver
    ADR-013). No toca `turno_asignacion` -- se resuelve en lectura."""

    def __init__(self, deps: CreateAsignacionOverrideDependencies) -> None:
        self._deps = deps

    async def execute(self, command: CreateAsignacionOverrideCommand) -> AsignacionOverrideDTO:
        await self._validar_campos(command)

        alcance: Literal["TOTAL"] | frozenset[uuid.UUID] = (
            "TOTAL" if command.slot_ids is None else frozenset(command.slot_ids)
        )
        existentes = await self._deps.overrides.list_activos_por_ausente(
            command.operador_ausente_id
        )
        if hay_solapamiento(command.desde, command.hasta, alcance, existentes):
            raise OverlappingOverrideError()

        override: TurnoAsignacionOverride = AsignacionOverride(
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

        involucrados = {command.operador_ausente_id, command.operador_reemplazante_id}
        users = await self._deps.users.get_users_by_ids(list(involucrados))
        return build_asignacion_override_dto(override, users)

    async def _validar_campos(self, command: CreateAsignacionOverrideCommand) -> None:
        if command.desde > command.hasta:
            raise InvalidOverrideRangeError()
        if command.operador_ausente_id == command.operador_reemplazante_id:
            raise OverrideMismoOperadorError()
        await validar_usuarios_existen(
            self._deps.users, [command.operador_ausente_id, command.operador_reemplazante_id]
        )
