from datetime import date
from typing import Literal

from src.shared.domain.value_objects.asignacion_override import AsignacionOverride


def resolver_override_aplicable[TOperadorId, TAlcanceId](
    operador_original: TOperadorId | None,
    criterio_alcance: TAlcanceId | None,
    fecha: date,
    overrides_del_ausente: list[AsignacionOverride[TOperadorId, TAlcanceId]],
) -> AsignacionOverride[TOperadorId, TAlcanceId] | None:
    """Override que aplica a `operador_original` en `fecha` para
    `criterio_alcance` (ver ADR-013): activo, vigente en `fecha` y cuyo
    alcance lo cubre (TOTAL, o ese elemento puntual). `overrides_del_ausente`
    ya viene filtrado por `operador_ausente_id == operador_original` (ver
    `list_activos_por_ausente`/`list_activos_por_ausentes` de cada
    repositorio) -- esta función solo filtra por vigencia y alcance, no por
    operador. `criterio_alcance` puede ser `None` (ej. un evento sin cliente
    asociado en contadores): en ese caso solo un override `TOTAL` matchea."""
    if operador_original is None:
        return None
    for override in overrides_del_ausente:
        if override.estado != "ACTIVA":
            continue
        if not (override.desde <= fecha <= override.hasta):
            continue
        if override.alcance == "TOTAL" or (
            criterio_alcance is not None and criterio_alcance in override.alcance
        ):
            return override
    return None


def resolver_operador_efectivo[TOperadorId, TAlcanceId](
    operador_original: TOperadorId | None,
    criterio_alcance: TAlcanceId | None,
    fecha: date,
    overrides_del_ausente: list[AsignacionOverride[TOperadorId, TAlcanceId]],
) -> TOperadorId | None:
    """"Operador efectivo en fecha X" (ver ADR-013): si hay un override
    aplicable devuelve el reemplazante; si no, el original sin cambios."""
    override = resolver_override_aplicable(
        operador_original, criterio_alcance, fecha, overrides_del_ausente
    )
    if override is None:
        return operador_original
    return override.operador_reemplazante_id


def hay_solapamiento[TOperadorId, TAlcanceId](
    desde: date,
    hasta: date,
    alcance: Literal["TOTAL"] | frozenset[TAlcanceId],
    existentes: list[AsignacionOverride[TOperadorId, TAlcanceId]],
) -> bool:
    """Dos overrides del mismo operador ausente conflictúan si sus rangos de
    fecha se superponen y comparten al menos un elemento en alcance (o
    alguno es TOTAL, que cubre cualquier elemento)."""
    for existente in existentes:
        if existente.desde > hasta or desde > existente.hasta:
            continue
        if alcance == "TOTAL" or existente.alcance == "TOTAL":
            return True
        if alcance & existente.alcance:
            return True
    return False
