from typing import Protocol


class OperadorColorLookup(Protocol):
    """Puerto que auth define para resolver, al dar de alta un usuario, el
    color de identidad que esa persona ya tiene como operador de Gestión (ver
    CreateUser). auth no puede importar `src.modules.contadores` (contrato
    `auth-independent-from-contadores` en `.importlinter`) — la implementación
    concreta vive fuera de ambos módulos, en `src/shared/infrastructure/`, que
    sí puede importar los dos. Este archivo es solo la interfaz: no sabe nada
    de Gestión ni de contadores."""

    async def find_color_by_nombre(self, nombre: str) -> str | None: ...
