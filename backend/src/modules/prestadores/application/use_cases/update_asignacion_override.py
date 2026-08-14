import uuid
from dataclasses import dataclass
from typing import Literal

from src.modules.prestadores.application.dtos.prestador_dtos import (
    AsignacionOverrideDTO,
    UpdateAsignacionOverrideCommand,
)
from src.modules.prestadores.application.use_cases.asignacion_override_dto_builder import (
    build_asignacion_override_dto,
)
from src.modules.prestadores.application.use_cases.asignacion_override_reglas import (
    hay_solapamiento,
)
from src.modules.prestadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.prestadores.domain.errors import (
    AsignacionOverrideNotFoundError,
    InvalidOverrideRangeError,
    OverlappingOverrideError,
    OverrideMismoOperadorError,
    OverrideNoEditableError,
)
from src.modules.prestadores.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
)
from src.modules.prestadores.domain.repositories.user_provider import UserProvider


@dataclass(frozen=True, slots=True)
class UpdateAsignacionOverrideDependencies:
    overrides: AsignacionOverrideRepository
    users: UserProvider


class UpdateAsignacionOverride:
    """Caso de uso: edita un override ACTIVA in-place (mismo `id` — ver
    ADR-013, actualización 2026-08-14). Un override CANCELADA es un registro
    histórico y no se puede editar; `estado` y `created_by_user_id` no
    cambian con la edición."""

    def __init__(self, deps: UpdateAsignacionOverrideDependencies) -> None:
        self._deps = deps

    async def execute(self, command: UpdateAsignacionOverrideCommand) -> AsignacionOverrideDTO:
        existing = await self._deps.overrides.get_by_id(command.override_id)
        if existing is None:
            raise AsignacionOverrideNotFoundError()
        if existing.estado != "ACTIVA":
            raise OverrideNoEditableError()
        _validar_campos(command)

        alcance: Literal["TOTAL"] | frozenset[uuid.UUID] = (
            "TOTAL" if command.prestador_ids is None else frozenset(command.prestador_ids)
        )
        await self._validar_solapamiento(command, alcance)

        override = AsignacionOverride(
            id=existing.id,
            operador_ausente_id=command.operador_ausente_id,
            operador_reemplazante_id=command.operador_reemplazante_id,
            desde=command.desde,
            hasta=command.hasta,
            alcance=alcance,
            estado="ACTIVA",
            motivo=command.motivo,
            created_by_user_id=existing.created_by_user_id,
        )
        await self._deps.overrides.update(override)

        involucrados = {command.operador_ausente_id, command.operador_reemplazante_id}
        users = await self._deps.users.get_users_by_ids(list(involucrados))
        return build_asignacion_override_dto(override, users)

    async def _validar_solapamiento(
        self,
        command: UpdateAsignacionOverrideCommand,
        alcance: Literal["TOTAL"] | frozenset[uuid.UUID],
    ) -> None:
        existentes = [
            o
            for o in await self._deps.overrides.list_activos_por_ausente(
                command.operador_ausente_id
            )
            if o.id != command.override_id  # el propio override no conflictúa consigo mismo
        ]
        if hay_solapamiento(command.desde, command.hasta, alcance, existentes):
            raise OverlappingOverrideError()


def _validar_campos(command: UpdateAsignacionOverrideCommand) -> None:
    if command.desde > command.hasta:
        raise InvalidOverrideRangeError()
    if command.operador_ausente_id == command.operador_reemplazante_id:
        raise OverrideMismoOperadorError()
