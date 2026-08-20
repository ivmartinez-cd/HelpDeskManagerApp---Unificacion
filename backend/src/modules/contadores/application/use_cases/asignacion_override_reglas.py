"""Validaciones de invariantes de overrides (ADR-013), compartidas entre
alta (`CreateAsignacionOverride`) y edición (`UpdateAsignacionOverride`).

`hay_solapamiento` vive en `src.shared.domain.services.asignacion_override_resolver`
desde que turnos se sumó como tercer módulo con el mismo patrón (ver ADR-013,
"revisar esta decisión si aparece un tercer módulo") -- acá solo queda
`validar_en_catalogo`, que es una regla propia de contadores (usernames de
Gestión sin FK, ver docstring)."""

from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.domain.errors import OperadorNoEncontradoError


def validar_en_catalogo(usernames: tuple[str, ...], operadores: dict[str, Operador]) -> None:
    """Los usernames son strings libres sin FK a `contadores_operadores` (la
    tabla se poda en cada sync, ver ADR-013): sin este chequeo un typo crea
    un override que nunca matchea ningún evento, sin error."""
    for username in usernames:
        if username not in operadores:
            raise OperadorNoEncontradoError(username)
