import re
from dataclasses import dataclass

from src.modules.auth.domain.errors import InvalidRoutePathError

_MAX_LENGTH = 128
_MAX_SEGMENTS = 4
_MAX_SEGMENT_LENGTH = 24
_SEGMENT = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


@dataclass(frozen=True, slots=True)
class RoutePath:
    """Ruta de navegación del frontend, normalizada y validada — es input de
    usuario que se persiste (tracking de accesos directos de Inicio), así que
    la forma se valida acá y no solo en el schema Pydantic del borde HTTP.

    Rechaza por construcción (el charset de `_SEGMENT` no admite `:`, `.`,
    `%`, `?`, `#`, `\\` ni segmentos vacíos): esquemas (`javascript:`,
    `data:`), links protocol-relative (`//evil.com`), query string, fragment
    y traversal (`..`). Un segmento que arranca con dígito o supera
    `_MAX_SEGMENT_LENGTH` además rechaza ids de detalle (`/liquidaciones/42`,
    un UUID de 36 caracteres) que de otro modo pasarían un charset
    alfanumérico-con-guiones sin ninguna regla más.
    """

    value: str

    def __post_init__(self) -> None:
        normalizado = self.value.strip().lower().rstrip("/")
        if not normalizado.startswith("/") or len(normalizado) > _MAX_LENGTH:
            raise InvalidRoutePathError(self.value)
        segmentos = normalizado[1:].split("/")
        if len(segmentos) > _MAX_SEGMENTS:
            raise InvalidRoutePathError(self.value)
        for segmento in segmentos:
            if len(segmento) > _MAX_SEGMENT_LENGTH or not _SEGMENT.match(segmento):
                raise InvalidRoutePathError(self.value)
        object.__setattr__(self, "value", normalizado)

    @property
    def module_key(self) -> str:
        return self.value[1:].split("/", 1)[0]
