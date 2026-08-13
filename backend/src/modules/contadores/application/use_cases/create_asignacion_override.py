import uuid
from dataclasses import dataclass
from datetime import date
from typing import Literal

from src.modules.contadores.application.dtos.asignacion_override_dto import AsignacionOverrideDTO
from src.modules.contadores.application.dtos.create_asignacion_override_request import (
    CreateAsignacionOverrideRequest,
)
from src.modules.contadores.application.use_cases.asignacion_override_dto_builder import (
    build_asignacion_override_dto,
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

        alcance: Literal["TOTAL"] | frozenset[str] = (
            "TOTAL" if request.clientes is None else frozenset(request.clientes)
        )
        existentes = await self._deps.overrides.list_activos_por_ausente(
            request.operador_ausente_id
        )
        if _hay_solapamiento(request.vigente_desde, request.vigente_hasta, alcance, existentes):
            raise OverlappingOverrideError()

        override = AsignacionOverride(
            id=uuid.uuid4(),
            operador_ausente_id=request.operador_ausente_id,
            operador_reemplazante_id=request.operador_reemplazante_id,
            vigente_desde=request.vigente_desde,
            vigente_hasta=request.vigente_hasta,
            alcance=alcance,
            estado="ACTIVA",
            motivo=request.motivo,
            created_by_user_id=request.created_by_user_id,
        )
        await self._deps.overrides.create(override)

        operadores = await self._deps.calendar.list_operadores()
        return build_asignacion_override_dto(override, {op.id: op for op in operadores})


def _hay_solapamiento(
    desde: date,
    hasta: date,
    alcance: Literal["TOTAL"] | frozenset[str],
    existentes: list[AsignacionOverride],
) -> bool:
    """Dos overrides del mismo operador ausente conflictúan si sus rangos de
    fecha se superponen y comparten al menos un cliente en alcance (o alguno
    es TOTAL, que cubre cualquier cliente)."""
    for existente in existentes:
        if existente.vigente_desde > hasta or desde > existente.vigente_hasta:
            continue
        if alcance == "TOTAL" or existente.alcance == "TOTAL":
            return True
        if alcance & existente.alcance:
            return True
    return False
