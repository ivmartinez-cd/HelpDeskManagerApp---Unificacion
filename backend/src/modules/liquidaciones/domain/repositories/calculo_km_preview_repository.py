"""Puerto de persistencia del preview del cálculo masivo de distancias."""

from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.calculo_km_preview import (
    CalculoKmPreview,
    PreviewFila,
)


class CalculoKmPreviewRepository(Protocol):
    async def create(
        self,
        *,
        prestador_id: UUID,
        filas: tuple[PreviewFila, ...],
        sin_ubicar: int,
        sin_ruta: int,
        elementos_google: int,
        sin_actividad: int,
    ) -> CalculoKmPreview:
        """Genera el `id` internamente y descarta previews anteriores del
        prestador — solo el último preview es aplicable."""
        ...

    async def get_by_id(self, preview_id: UUID) -> CalculoKmPreview | None: ...

    async def delete(self, preview_id: UUID) -> bool: ...
