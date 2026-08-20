import uuid
from dataclasses import dataclass

from src.modules.turnos.domain.errors import IntercambioNotFoundError
from src.modules.turnos.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
)


@dataclass(frozen=True, slots=True)
class CancelIntercambioDependencies:
    overrides: AsignacionOverrideRepository


class CancelIntercambio:
    """Caso de uso: cancela las dos coberturas de un intercambio (ADR-026)
    -- nunca queda media permuta. Sin `DELETE`, igual que ADR-013: el par
    queda como registro histórico cancelado."""

    def __init__(self, deps: CancelIntercambioDependencies) -> None:
        self._deps = deps

    async def execute(self, intercambio_id: uuid.UUID) -> None:
        par = await self._deps.overrides.list_by_intercambio(intercambio_id)
        if not par:
            raise IntercambioNotFoundError()
        for override in par:
            await self._deps.overrides.cancelar(override.id)
