"""Puerto de sub-prestadores (spsts)."""

from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.spst import Spst


class SpstRepository(Protocol):
    async def get_by_id(self, spst_id: UUID) -> Spst | None: ...

    async def list_by_prestador(self, prestador_id: UUID) -> list[Spst]: ...

    async def list_all(
        self, *, prestador_id: UUID | None = None, solo_activos: bool = False
    ) -> list[Spst]: ...

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

    async def vincular_base_sucursal(
        self, spst_id: UUID, *, siges_base_sucursal_id: int | None
    ) -> Spst | None: ...

    async def vincular_siges(self, spst_id: UUID, *, siges_empresa_id: int | None) -> Spst | None:
        """Establece (o quita, con None) el vínculo a `dbo.Empresa` de Siges
        (ADR-014). Lanza `SigesVinculoDuplicadoError` si el id ya vincula a otro
        SPST."""
        ...

    async def delete(self, spst_id: UUID) -> bool: ...
