import uuid

from src.modules.prestadores.application.dtos.prestador_dtos import AsignacionOverrideDTO
from src.modules.prestadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.prestadores.domain.repositories.user_provider import UserInfo


def build_asignacion_override_dto(
    override: AsignacionOverride, users: dict[uuid.UUID, UserInfo]
) -> AsignacionOverrideDTO:
    ausente = users.get(override.operador_ausente_id)
    reemplazante = users.get(override.operador_reemplazante_id)
    if override.alcance == "TOTAL":
        alcance_total, prestador_ids = True, []
    else:
        alcance_total, prestador_ids = False, sorted(override.alcance, key=str)
    return AsignacionOverrideDTO(
        id=override.id,
        operador_ausente_id=override.operador_ausente_id,
        operador_ausente_nombre=ausente.full_name if ausente else None,
        operador_reemplazante_id=override.operador_reemplazante_id,
        operador_reemplazante_nombre=reemplazante.full_name if reemplazante else None,
        desde=override.desde,
        hasta=override.hasta,
        alcance_total=alcance_total,
        prestador_ids=prestador_ids,
        estado=override.estado,
        motivo=override.motivo,
    )
