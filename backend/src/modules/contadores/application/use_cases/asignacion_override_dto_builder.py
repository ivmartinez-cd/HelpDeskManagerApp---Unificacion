from src.modules.contadores.application.dtos.asignacion_override_dto import AsignacionOverrideDTO
from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.contadores.domain.entities.operador import Operador


def build_asignacion_override_dto(
    override: AsignacionOverride, operadores_por_id: dict[str, Operador]
) -> AsignacionOverrideDTO:
    ausente = operadores_por_id.get(override.operador_ausente_id)
    reemplazante = operadores_por_id.get(override.operador_reemplazante_id)
    if override.alcance == "TOTAL":
        alcance_total, clientes = True, []
    else:
        alcance_total, clientes = False, sorted(override.alcance)
    return AsignacionOverrideDTO(
        id=override.id,
        operador_ausente_id=override.operador_ausente_id,
        operador_ausente_nombre=ausente.nombre if ausente else None,
        operador_reemplazante_id=override.operador_reemplazante_id,
        operador_reemplazante_nombre=reemplazante.nombre if reemplazante else None,
        vigente_desde=override.desde,
        vigente_hasta=override.hasta,
        alcance_total=alcance_total,
        clientes=clientes,
        estado=override.estado,
        motivo=override.motivo,
    )
