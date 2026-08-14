"""Validaciones de invariantes de overrides (ADR-013), compartidas entre
alta (`CreateAsignacionOverride`) y edición (`UpdateAsignacionOverride`)."""

import uuid
from datetime import date
from typing import Literal

from src.modules.prestadores.domain.entities.asignacion_override import AsignacionOverride


def hay_solapamiento(
    desde: date,
    hasta: date,
    alcance: Literal["TOTAL"] | frozenset[uuid.UUID],
    existentes: list[AsignacionOverride],
) -> bool:
    """Dos overrides del mismo operador ausente conflictúan si sus rangos de
    fecha se superponen y comparten al menos un PST en alcance (o alguno es
    TOTAL, que cubre cualquier PST)."""
    for existente in existentes:
        if existente.desde > hasta or desde > existente.hasta:
            continue
        if alcance == "TOTAL" or existente.alcance == "TOTAL":
            return True
        if alcance & existente.alcance:
            return True
    return False
