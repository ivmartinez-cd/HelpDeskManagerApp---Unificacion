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

    async def update(
        self,
        prestador_id: UUID,
        *,
        nombre: str,
        nombre_corto: str,
        cuit: str | None,
        region: str | None,
    ) -> Prestador | None: ...

    async def toggle_activo(self, prestador_id: UUID, *, activo: bool) -> Prestador | None: ...

    async def vincular_siges(
        self, prestador_id: UUID, *, siges_empresa_id: int | None
    ) -> Prestador | None:
        """Establece (o quita, con None) el vínculo a `dbo.Empresa` de Siges
        (ADR-014). Lanza `SigesVinculoDuplicadoError` si el id ya vincula a otro
        prestador."""
        ...

    async def delete(self, prestador_id: UUID) -> bool:
        """Baja física. Lanza `PrestadorConLiquidacionesError` si tiene liquidaciones
        asociadas (`liquidaciones.prestador_id` no cascadea a propósito)."""
        ...
