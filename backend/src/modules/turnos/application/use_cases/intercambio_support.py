"""Piezas compartidas por los casos de uso de intercambio de turnos
(ADR-026): un intercambio son dos coberturas ADR-013 cruzadas (A ausente →
B cubre, B ausente → A cubre) con el mismo `intercambio_id`, que se crean,
editan y cancelan juntas. El resolver no cambia -- resuelve un solo salto
por franja, así que el par ya produce el efecto buscado."""

import uuid
from dataclasses import dataclass
from typing import Literal

from src.modules.turnos.application.dtos.turno_dtos import (
    AsignacionOverrideDTO,
    IntercambioCommand,
    IntercambioDTO,
)
from src.modules.turnos.application.use_cases.asignacion_override_dto_builder import (
    build_asignacion_override_dto,
)
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

MOTIVO_INTERCAMBIO_DEFAULT = "Intercambio"


@dataclass(frozen=True, slots=True)
class IntercambioDependencies:
    overrides: AsignacionOverrideRepository
    users: UserProvider


def validar_campos_intercambio(command: IntercambioCommand) -> None:
    if command.desde > command.hasta:
        raise InvalidOverrideRangeError()
    if command.operador_a_id == command.operador_b_id:
        raise OverrideMismoOperadorError()


def _alcance(slot_ids: list[uuid.UUID] | None) -> Literal["TOTAL"] | frozenset[uuid.UUID]:
    return "TOTAL" if slot_ids is None else frozenset(slot_ids)


def armar_par(
    command: IntercambioCommand,
    intercambio_id: uuid.UUID,
    ids: tuple[uuid.UUID, uuid.UUID],
    created_by_user_id: uuid.UUID,
) -> tuple[TurnoAsignacionOverride, TurnoAsignacionOverride]:
    """Las dos coberturas cruzadas del intercambio, en el orden del DTO:
    [A ausente → B cubre (franjas de A), B ausente → A cubre (franjas de B)]."""
    motivo = (command.motivo or "").strip() or MOTIVO_INTERCAMBIO_DEFAULT

    def lado(
        oid: uuid.UUID, ausente: uuid.UUID, cubre: uuid.UUID, slot_ids: list[uuid.UUID] | None
    ) -> TurnoAsignacionOverride:
        return AsignacionOverride(
            id=oid,
            operador_ausente_id=ausente,
            operador_reemplazante_id=cubre,
            desde=command.desde,
            hasta=command.hasta,
            alcance=_alcance(slot_ids),
            estado="ACTIVA",
            motivo=motivo,
            created_by_user_id=created_by_user_id,
            intercambio_id=intercambio_id,
        )

    return (
        lado(ids[0], command.operador_a_id, command.operador_b_id, command.slot_ids_a),
        lado(ids[1], command.operador_b_id, command.operador_a_id, command.slot_ids_b),
    )


async def validar_sin_solapamiento(
    overrides: AsignacionOverrideRepository,
    override: TurnoAsignacionOverride,
    excluir_ids: set[uuid.UUID],
) -> None:
    """Mismo criterio que el alta/edición de una cobertura común: cada lado
    del intercambio no puede pisar otra cobertura activa del mismo ausente.
    `excluir_ids` = las dos filas del propio par al editar."""
    existentes = [
        o
        for o in await overrides.list_activos_por_ausente(override.operador_ausente_id)
        if o.id not in excluir_ids
    ]
    if hay_solapamiento(override.desde, override.hasta, override.alcance, existentes):
        raise OverlappingOverrideError()


async def build_intercambio_dto(
    users: UserProvider,
    intercambio_id: uuid.UUID,
    par: list[TurnoAsignacionOverride],
) -> IntercambioDTO:
    involucrados = {o.operador_ausente_id for o in par} | {
        o.operador_reemplazante_id for o in par
    }
    nombres = await users.get_users_by_ids(list(involucrados))
    coberturas: list[AsignacionOverrideDTO] = [
        build_asignacion_override_dto(o, nombres) for o in par
    ]
    return IntercambioDTO(intercambio_id=intercambio_id, coberturas=coberturas)
