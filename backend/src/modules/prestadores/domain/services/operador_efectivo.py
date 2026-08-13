import uuid
from datetime import date

from src.modules.prestadores.domain.entities.asignacion_override import AsignacionOverride


def resolver_operador_efectivo(
    operador_original: uuid.UUID | None,
    prestador_id: uuid.UUID,
    fecha: date,
    overrides_del_ausente: list[AsignacionOverride],
) -> uuid.UUID | None:
    """"Operador efectivo en fecha X" (ver ADR-013): si `operador_original`
    tiene un override activo y vigente en `fecha` cuyo alcance cubre a
    `prestador_id` (TOTAL o el PST puntual), devuelve el reemplazante; si no,
    el original sin cambios. `overrides_del_ausente` ya viene filtrado por
    `operador_ausente_id == operador_original` (ver
    AsignacionOverrideRepository.list_activos_por_ausente) — esta función solo
    filtra por vigencia y alcance, no por operador."""
    if operador_original is None:
        return None
    for override in overrides_del_ausente:
        if override.estado != "ACTIVA":
            continue
        if not (override.desde <= fecha <= override.hasta):
            continue
        if override.alcance == "TOTAL" or prestador_id in override.alcance:
            return override.operador_reemplazante_id
    return operador_original
