"""Puerto de modificaciones del prestador (modificaciones_prestador) — ver
ADR-038 y `domain/entities/modificacion_prestador.py`."""

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.modificacion_prestador import (
    ModificacionPrestador,
)


class ModificacionPrestadorRepository(Protocol):
    async def bulk_create(self, modificaciones: Sequence[ModificacionPrestador]) -> None: ...

    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[ModificacionPrestador]:
        """Orden `detectada_en` descendente — el router pagina en memoria con
        `Page.of`, mismo patrón que `list_liquidaciones`."""
        ...

    async def list_no_vistas(self) -> list[ModificacionPrestador]:
        """No vistas de todas las liquidaciones, orden `detectada_en`
        descendente — el frontend usa el total para el badge del menú."""
        ...

    async def marcar_vistas(self, liquidacion_id: UUID) -> int:
        """Pisa `vista_en` con `now()` en las no vistas de la liquidación.
        Devuelve la cantidad actualizada."""
        ...
