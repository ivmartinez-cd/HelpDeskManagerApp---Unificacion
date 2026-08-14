from dataclasses import dataclass
from typing import Literal

from src.modules.contadores.application.dtos.asignacion_override_dto import AsignacionOverrideDTO
from src.modules.contadores.application.dtos.update_asignacion_override_request import (
    UpdateAsignacionOverrideRequest,
)
from src.modules.contadores.application.use_cases.asignacion_override_dto_builder import (
    build_asignacion_override_dto,
)
from src.modules.contadores.application.use_cases.asignacion_override_reglas import (
    hay_solapamiento,
    validar_en_catalogo,
)
from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.contadores.domain.errors import (
    AsignacionOverrideNotFoundError,
    InvalidOverrideRangeError,
    OverlappingOverrideError,
    OverrideMismoOperadorError,
    OverrideNoEditableError,
)
from src.modules.contadores.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
)
from src.modules.contadores.domain.repositories.calendar_event_repository import (
    CalendarEventRepository,
)


@dataclass(frozen=True, slots=True)
class UpdateAsignacionOverrideDependencies:
    overrides: AsignacionOverrideRepository
    calendar: CalendarEventRepository


class UpdateAsignacionOverride:
    """Caso de uso: edita un override ACTIVA in-place (mismo `id` — ver
    ADR-013, actualización 2026-08-14). Un override CANCELADA es un registro
    histórico y no se puede editar; `estado` y `created_by_user_id` no
    cambian con la edición."""

    def __init__(self, deps: UpdateAsignacionOverrideDependencies) -> None:
        self._deps = deps

    async def execute(self, request: UpdateAsignacionOverrideRequest) -> AsignacionOverrideDTO:
        existing = await self._deps.overrides.get_by_id(request.override_id)
        if existing is None:
            raise AsignacionOverrideNotFoundError()
        if existing.estado != "ACTIVA":
            raise OverrideNoEditableError()
        _validar_campos(request)

        operadores = {op.id: op for op in await self._deps.calendar.list_operadores()}
        validar_en_catalogo(
            (request.operador_ausente_id, request.operador_reemplazante_id), operadores
        )

        alcance: Literal["TOTAL"] | frozenset[str] = (
            "TOTAL" if request.clientes is None else frozenset(request.clientes)
        )
        await self._validar_solapamiento(request, alcance)

        override = AsignacionOverride(
            id=existing.id,
            operador_ausente_id=request.operador_ausente_id,
            operador_reemplazante_id=request.operador_reemplazante_id,
            vigente_desde=request.vigente_desde,
            vigente_hasta=request.vigente_hasta,
            alcance=alcance,
            estado="ACTIVA",
            motivo=request.motivo,
            created_by_user_id=existing.created_by_user_id,
        )
        await self._deps.overrides.update(override)
        return build_asignacion_override_dto(override, operadores)

    async def _validar_solapamiento(
        self,
        request: UpdateAsignacionOverrideRequest,
        alcance: Literal["TOTAL"] | frozenset[str],
    ) -> None:
        existentes = [
            o
            for o in await self._deps.overrides.list_activos_por_ausente(
                request.operador_ausente_id
            )
            if o.id != request.override_id  # el propio override no conflictúa consigo mismo
        ]
        if hay_solapamiento(request.vigente_desde, request.vigente_hasta, alcance, existentes):
            raise OverlappingOverrideError()


def _validar_campos(request: UpdateAsignacionOverrideRequest) -> None:
    if request.vigente_desde > request.vigente_hasta:
        raise InvalidOverrideRangeError()
    if request.operador_ausente_id == request.operador_reemplazante_id:
        raise OverrideMismoOperadorError()
