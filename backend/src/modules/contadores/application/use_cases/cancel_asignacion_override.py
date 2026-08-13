import uuid
from dataclasses import dataclass

from src.modules.contadores.domain.errors import AsignacionOverrideNotFoundError
from src.modules.contadores.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
)


@dataclass(frozen=True, slots=True)
class CancelAsignacionOverrideDependencies:
    overrides: AsignacionOverrideRepository


class CancelAsignacionOverride:
    """Caso de uso: cancela un override antes de que venza. No hay `DELETE`
    — cancelar es la única forma de revertir antes de `vigente_hasta`, para
    no perder el registro de que el override existió (ver ADR-013)."""

    def __init__(self, deps: CancelAsignacionOverrideDependencies) -> None:
        self._deps = deps

    async def execute(self, override_id: uuid.UUID) -> None:
        existing = await self._deps.overrides.get_by_id(override_id)
        if existing is None:
            raise AsignacionOverrideNotFoundError()
        await self._deps.overrides.cancelar(override_id)
