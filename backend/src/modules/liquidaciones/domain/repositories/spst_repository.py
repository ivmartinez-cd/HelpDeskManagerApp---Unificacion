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

    async def update(
        self,
        spst_id: UUID,
        *,
        nombre: str,
        domicilio: str | None,
        localidad: str | None,
        provincia: str | None,
        zona: str | None,
    ) -> Spst | None: ...

    async def toggle_activo(self, spst_id: UUID, *, activo: bool) -> Spst | None: ...

    async def delete(self, spst_id: UUID) -> bool: ...
