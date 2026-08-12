"""Puerto de sub-prestadores (spsts)."""

from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.spst import Spst


class SpstRepository(Protocol):
    async def get_by_id(self, spst_id: UUID) -> Spst | None: ...

    async def list_by_prestador(self, prestador_id: UUID) -> list[Spst]: ...

    async def create(
        self,
        *,
        prestador_id: UUID,
        nombre: str,
        domicilio: str | None,
        localidad: str | None,
        provincia: str | None,
        zona: str | None,
    ) -> Spst:
        """Genera el `id` (UUID) internamente."""
        ...
