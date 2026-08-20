import uuid
from datetime import date
from typing import Protocol

from src.modules.turnos.domain.entities.asignacion import Asignacion


class AsignacionRepository(Protocol):
    """Puerto de persistencia para asignaciones de usuario a slots."""

    async def list_by_slots(
        self, slot_ids: list[uuid.UUID], target_date: date
    ) -> dict[uuid.UUID, list[Asignacion]]:
        """Asignaciones vigentes en `target_date` para cada slot -- evita N+1 al listar
        todos los slots de una casilla (o de todas)."""
        ...

    async def list_active_on_date(self, target_date: date) -> list[Asignacion]: ...

    async def replace_for_slot(
        self, slot_id: uuid.UUID, effective_date: date, asignaciones: list[Asignacion]
    ) -> None:
        """Reemplaza los operadores de un slot a partir de `effective_date`: cierra
        (`vigente_hasta`) las asignaciones vigentes anteriores en vez de borrarlas, para
        no perder el historial de quién cubrió el slot antes. `asignaciones` puede venir
        vacía (desasignar todos)."""
        ...

    async def delete_by_slot(self, slot_id: uuid.UUID) -> None: ...
