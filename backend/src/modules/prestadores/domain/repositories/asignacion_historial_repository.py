import uuid
from datetime import date
from typing import Protocol

from src.modules.prestadores.domain.entities.asignacion_historial import AsignacionHistorial


class AsignacionHistorialRepository(Protocol):
    """Puerto de persistencia del historial de reasignación de operador por PST."""

    async def list_by_prestador(self, prestador_id: uuid.UUID) -> list[AsignacionHistorial]: ...

    async def reasignar(
        self, prestador_id: uuid.UUID, operador_id: uuid.UUID | None, desde: date
    ) -> None:
        """Cierra el tramo vigente (si hay uno) en `desde - 1 día` y abre un
        tramo nuevo con el operador indicado. Si el tramo vigente empezó en
        `desde` o después, se borra en vez de cerrarse con un rango inválido
        (mismo criterio que `AsignacionRepository.replace_for_slot` de
        turnos)."""
        ...
