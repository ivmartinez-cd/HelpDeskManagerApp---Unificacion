import uuid
from datetime import date
from typing import Protocol

from src.modules.prestadores.domain.entities.asignacion_historial import AsignacionHistorial


class AsignacionHistorialRepository(Protocol):
    """Puerto de persistencia del historial de reasignación de operador por PST."""

    async def list_by_prestador(self, prestador_id: uuid.UUID) -> list[AsignacionHistorial]: ...

    async def list_vigentes_a(self, fecha: date) -> dict[uuid.UUID, uuid.UUID | None]:
        """Operador real de cada PST a `fecha` según el historial
        (`prestador_id -> operador_id`). Un PST sin tramo que cubra la fecha
        no aparece en el dict."""
        ...

    async def reasignar(
        self, prestador_id: uuid.UUID, operador_id: uuid.UUID | None, desde: date
    ) -> None:
        """Abre un tramo nuevo en `desde` con el operador indicado y deja el
        historial sin solapes (ver `planificar_reasignacion`): los tramos que
        alcanzan `desde` se cierran en `desde - 1 día` y los que empiezan en
        `desde` o después se borran (mismo criterio que
        `AsignacionRepository.replace_for_slot` de turnos)."""
        ...
