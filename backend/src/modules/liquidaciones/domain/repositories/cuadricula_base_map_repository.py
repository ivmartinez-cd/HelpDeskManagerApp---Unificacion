"""Puerto del mapeo cuadrícula-Siges → sucursal-base del PST."""

from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.cuadricula_base_map import CuadriculaBaseMap


class CuadriculaBaseMapRepository(Protocol):
    async def list_by_prestador(self, prestador_id: UUID) -> list[CuadriculaBaseMap]: ...

    async def upsert(
        self,
        *,
        prestador_id: UUID,
        cuadricula: str,
        siges_base_sucursal_id: int,
    ) -> CuadriculaBaseMap:
        """Crea o pisa el mapeo del par (prestador, cuadrícula)."""
        ...

    async def delete(self, *, prestador_id: UUID, cuadricula: str) -> None: ...
