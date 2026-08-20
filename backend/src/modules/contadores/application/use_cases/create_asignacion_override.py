import uuid
from dataclasses import dataclass
from typing import Literal

from src.modules.contadores.application.dtos.asignacion_override_dto import AsignacionOverrideDTO
from src.modules.contadores.application.dtos.create_asignacion_override_request import (
    CreateAsignacionOverrideRequest,
)
from src.modules.contadores.application.use_cases.asignacion_override_dto_builder import (
    build_asignacion_override_dto,
)
from src.modules.contadores.application.use_cases.asignacion_override_reglas import (
    validar_en_catalogo,
)
from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.contadores.domain.errors import (
    InvalidOverrideRangeError,
    OverlappingOverrideError,
    OverrideMismoOperadorError,
)
from src.modules.contadores.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
)
from src.modules.contadores.domain.repositories.calendar_event_repository import (
    CalendarEventRepository,
)
from src.shared.domain.services.asignacion_override_resolver import hay_solapamiento


@dataclass(frozen=True, slots=True)
class CreateAsignacionOverrideDependencies:
    overrides: AsignacionOverrideRepository
    calendar: CalendarEventRepository


class CreateAsignacionOverride:
    """Caso de uso: da de alta un override temporal de asignación (ver
    ADR-013). No toca ni los eventos sincronizados ni `contadores_operadores`."""

    def __init__(self, deps: CreateAsignacionOverrideDependencies) -> None:
        self._deps = deps

    async def execute(self, request: CreateAsignacionOverrideRequest) -> AsignacionOverrideDTO:
        if request.vigente_desde > request.vigente_hasta:
            raise InvalidOverrideRangeError()
        if request.operador_ausente_id == request.operador_reemplazante_id:
            raise OverrideMismoOperadorError()

        operadores = {op.id: op for op in await self._deps.calendar.list_operadores()}
        validar_en_catalogo(
            (request.operador_ausente_id, request.operador_reemplazante_id), operadores
        )

        alcance: Literal["TOTAL"] | frozenset[str] = (
            "TOTAL" if request.clientes is None else frozenset(request.clientes)
        )
        existentes = await self._deps.overrides.list_activos_por_ausente(
            request.operador_ausente_id
        )
        if hay_solapamiento(request.vigente_desde, request.vigente_hasta, alcance, existentes):
            raise OverlappingOverrideError()

        override = AsignacionOverride(
            id=uuid.uuid4(),
            operador_ausente_id=request.operador_ausente_id,
            operador_reemplazante_id=request.operador_reemplazante_id,
            desde=request.vigente_desde,
            hasta=request.vigente_hasta,
            alcance=alcance,
            estado="ACTIVA",
            motivo=request.motivo,
            created_by_user_id=request.created_by_user_id,
        )
        await self._deps.overrides.create(override)
        return build_asignacion_override_dto(override, operadores)
