"""Validaciones de invariantes de overrides (ADR-013), compartidas entre
alta (`CreateAsignacionOverride`) y edición (`UpdateAsignacionOverride`)."""

from datetime import date
from typing import Literal

from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.domain.errors import OperadorNoEncontradoError


def validar_en_catalogo(usernames: tuple[str, ...], operadores: dict[str, Operador]) -> None:
    """Los usernames son strings libres sin FK a `contadores_operadores` (la
    tabla se poda en cada sync, ver ADR-013): sin este chequeo un typo crea
    un override que nunca matchea ningún evento, sin error."""
    for username in usernames:
        if username not in operadores:
            raise OperadorNoEncontradoError(username)


def hay_solapamiento(
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
