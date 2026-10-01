import uuid

from src.modules.turnos.application.dtos.turno_dtos import AsignacionOverrideDTO
from src.modules.turnos.domain.repositories.asignacion_override_repository import (
    TurnoAsignacionOverride,
)
from src.modules.turnos.domain.repositories.user_provider import UserInfo, UserProvider


def build_asignacion_override_dto(
    override: TurnoAsignacionOverride, users: dict[uuid.UUID, UserInfo]
) -> AsignacionOverrideDTO:
    ausente = users.get(override.operador_ausente_id)
    reemplazante = users.get(override.operador_reemplazante_id)
    if override.alcance == "TOTAL":
        alcance_total, slot_ids = True, []
    else:
        alcance_total, slot_ids = False, sorted(override.alcance, key=str)
    return AsignacionOverrideDTO(
        id=override.id,
        operador_ausente_id=override.operador_ausente_id,
        operador_ausente_nombre=ausente.full_name if ausente else None,
        operador_reemplazante_id=override.operador_reemplazante_id,
        operador_reemplazante_nombre=reemplazante.full_name if reemplazante else None,
        desde=override.desde,
        hasta=override.hasta,
        alcance_total=alcance_total,
        slot_ids=slot_ids,
        estado=override.estado,
        motivo=override.motivo,
        intercambio_id=override.intercambio_id,
    )


async def build_asignacion_override_dto_con_usuarios(
    override: TurnoAsignacionOverride, users: UserProvider
) -> AsignacionOverrideDTO:
    """Resuelve los nombres de ausente y reemplazante y arma el DTO."""
    involucrados = {override.operador_ausente_id, override.operador_reemplazante_id}
    return build_asignacion_override_dto(
        override, await users.get_users_by_ids(list(involucrados))
    )
