import uuid
from dataclasses import dataclass
from typing import Literal

from src.modules.turnos.application.dtos.turno_dtos import (
    AsignacionOverrideDTO,
    UpdateAsignacionOverrideCommand,
)
from src.modules.turnos.application.use_cases.asignacion_override_dto_builder import (
    build_asignacion_override_dto,
)
from src.modules.turnos.domain.errors import (
    AsignacionOverrideNotFoundError,
    InvalidOverrideRangeError,
    OverlappingOverrideError,
    OverrideEsIntercambioError,
    OverrideMismoOperadorError,
    OverrideNoEditableError,
)
from src.modules.turnos.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
    TurnoAsignacionOverride,
)
from src.modules.turnos.domain.repositories.user_provider import UserProvider
from src.shared.domain.services.asignacion_override_resolver import hay_solapamiento
from src.shared.domain.value_objects.asignacion_override import AsignacionOverride


@dataclass(frozen=True, slots=True)
class UpdateAsignacionOverrideDependencies:
    overrides: AsignacionOverrideRepository
    users: UserProvider


class UpdateAsignacionOverride:
    """Caso de uso: edita una cobertura ACTIVA in-place (mismo `id` -- ver
    ADR-013, actualización 2026-08-14). Una cobertura CANCELADA es un
    registro histórico y no se puede editar; `estado` y `created_by_user_id`
    no cambian con la edición."""

    def __init__(self, deps: UpdateAsignacionOverrideDependencies) -> None:
        self._deps = deps

    async def execute(self, command: UpdateAsignacionOverrideCommand) -> AsignacionOverrideDTO:
        existing = await self._deps.overrides.get_by_id(command.override_id)
        if existing is None:
            raise AsignacionOverrideNotFoundError()
        if existing.estado != "ACTIVA":
            raise OverrideNoEditableError()
        if existing.intercambio_id is not None:
            # Una mitad de intercambio (ADR-026) se edita por el par completo.
            raise OverrideEsIntercambioError()
        _validar_campos(command)

        alcance: Literal["TOTAL"] | frozenset[uuid.UUID] = (
            "TOTAL" if command.slot_ids is None else frozenset(command.slot_ids)
        )
        await self._validar_solapamiento(command, alcance)

        override: TurnoAsignacionOverride = AsignacionOverride(
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
            if o.id != command.override_id  # la propia cobertura no conflictúa consigo misma
        ]
        if hay_solapamiento(command.desde, command.hasta, alcance, existentes):
            raise OverlappingOverrideError()


def _validar_campos(command: UpdateAsignacionOverrideCommand) -> None:
    if command.desde > command.hasta:
        raise InvalidOverrideRangeError()
    if command.operador_ausente_id == command.operador_reemplazante_id:
        raise OverrideMismoOperadorError()
