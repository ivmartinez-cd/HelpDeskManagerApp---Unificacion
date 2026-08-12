"""Puerto de decisiones de la Team Leader sobre una alerta (resoluciones)."""

from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.resolucion import Resolucion


class ResolucionRepository(Protocol):
    async def list_by_alerta(self, alerta_id: UUID) -> list[Resolucion]: ...

    async def create(
        self, *, alerta_id: UUID, decision: str, justificacion: str | None, comentario: str | None
    ) -> Resolucion:
        """Genera el `id` (UUID) internamente."""
        ...
