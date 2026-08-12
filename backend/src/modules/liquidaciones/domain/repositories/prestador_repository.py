"""Puerto de prestadores (prestadores)."""

from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.prestador import Prestador


class PrestadorRepository(Protocol):
    async def get_by_id(self, prestador_id: UUID) -> Prestador | None: ...

    async def get_by_nombre_corto(self, nombre_corto: str) -> Prestador | None:
        """`nombre_corto` es unique — usado al importar Excel/CSV para resolver o
        rechazar el prestador de destino sin ambigüedad."""
        ...

    async def list_all(self, *, solo_activos: bool = False) -> list[Prestador]: ...

    async def create(
        self, *, nombre: str, nombre_corto: str, cuit: str | None, region: str | None
    ) -> Prestador:
        """Genera el `id` (UUID) internamente — el caller no lo conoce de antemano."""
        ...
