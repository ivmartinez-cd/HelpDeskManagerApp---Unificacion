import uuid
from typing import Protocol

from src.shared.domain.value_objects.asignacion_override import AsignacionOverride

TurnoAsignacionOverride = AsignacionOverride[uuid.UUID, uuid.UUID]
"""Operador ausente/reemplazante = `app_user.id`; alcance parcial = `turno_slot.id`."""


class AsignacionOverrideRepository(Protocol):
    """Puerto de persistencia de coberturas temporales de turnos (ver ADR-013)."""

    async def create(self, override: TurnoAsignacionOverride) -> None: ...

    async def list_all(self) -> list[TurnoAsignacionOverride]: ...

    async def get_by_id(self, override_id: uuid.UUID) -> TurnoAsignacionOverride | None: ...

    async def list_activos_por_ausente(
        self, operador_ausente_id: uuid.UUID
    ) -> list[TurnoAsignacionOverride]:
        """Coberturas con estado ACTIVA para ese operador ausente, sin filtrar
        por fecha -- catálogo chico por operador, el filtro de vigencia lo
        hace `resolver_operador_efectivo`."""
        ...

    async def list_activos_por_ausentes(
        self, operador_ausente_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[TurnoAsignacionOverride]]:
        """Batch de `list_activos_por_ausente` -- evita N+1 al resolver
        `GetCurrentShifts`, mismo criterio que `AsignacionRepository.list_by_slots`."""
        ...

    async def update(self, override: TurnoAsignacionOverride) -> None:
        """Reemplaza los datos de la cobertura (mismo `id`), incluido el
        alcance. No toca `created_by_user_id` ni `estado` -- la única
        transición de estado es `cancelar`."""
        ...

    async def cancelar(self, override_id: uuid.UUID) -> None: ...
