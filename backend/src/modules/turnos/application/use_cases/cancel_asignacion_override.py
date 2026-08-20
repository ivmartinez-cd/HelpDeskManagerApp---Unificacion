import uuid
from dataclasses import dataclass

from src.modules.turnos.domain.errors import AsignacionOverrideNotFoundError
from src.modules.turnos.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
)


@dataclass(frozen=True, slots=True)
class CancelAsignacionOverrideDependencies:
    overrides: AsignacionOverrideRepository


class CancelAsignacionOverride:
    """Caso de uso: cancela una cobertura antes de que venza. No hay
    `DELETE` -- cancelar es la única forma de revertir antes de `hasta`,
    para no perder el registro de que la cobertura existió (ver ADR-013).
    Si la cobertura es una mitad de un intercambio (ADR-026), se cancela el
    par completo: nunca queda media permuta vigente."""

    def __init__(self, deps: CancelAsignacionOverrideDependencies) -> None:
        self._deps = deps

    async def execute(self, override_id: uuid.UUID) -> None:
        existing = await self._deps.overrides.get_by_id(override_id)
        if existing is None:
            raise AsignacionOverrideNotFoundError()
        if existing.intercambio_id is None:
            await self._deps.overrides.cancelar(override_id)
            return
        for mitad in await self._deps.overrides.list_by_intercambio(existing.intercambio_id):
            await self._deps.overrides.cancelar(mitad.id)
