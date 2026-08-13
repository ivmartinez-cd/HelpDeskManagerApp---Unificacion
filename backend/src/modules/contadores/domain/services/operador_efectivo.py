from datetime import date

from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride


def resolver_override_aplicable(
    operador_original: str | None,
    cliente: str | None,
    fecha: date,
    overrides_del_ausente: list[AsignacionOverride],
) -> AsignacionOverride | None:
    """Override que aplica a un evento de `operador_original` en `fecha`
    (ver ADR-013): activo, vigente en `fecha` y cuyo alcance cubre a
    `cliente` (TOTAL o ese cliente puntual). `overrides_del_ausente` ya viene
    filtrado por `operador_ausente_id == operador_original` (ver
    AsignacionOverrideRepository.list_activos_por_ausente) — esta función solo
    filtra por vigencia y alcance, no por operador. El matching por `cliente`
    es por igualdad exacta de string (texto libre, sin catálogo), así que
    variaciones de nombre entre eventos del mismo cliente real no matchean."""
    if operador_original is None:
        return None
    for override in overrides_del_ausente:
        if override.estado != "ACTIVA":
            continue
        if not (override.vigente_desde <= fecha <= override.vigente_hasta):
            continue
        if override.alcance == "TOTAL" or (cliente is not None and cliente in override.alcance):
            return override
    return None


def resolver_operador_efectivo(
    operador_original: str | None,
    cliente: str | None,
    fecha: date,
    overrides_del_ausente: list[AsignacionOverride],
) -> str | None:
    """"Operador efectivo en fecha X" (ver ADR-013): si hay un override
    aplicable devuelve el reemplazante; si no, el original sin cambios."""
    override = resolver_override_aplicable(operador_original, cliente, fecha, overrides_del_ausente)
    if override is None:
        return operador_original
    return override.operador_reemplazante_id
