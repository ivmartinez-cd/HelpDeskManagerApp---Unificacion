"""Puerto de preliquidaciones importadas (liquidaciones)."""

from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion


class LiquidacionRepository(Protocol):
    async def get_by_id(self, liquidacion_id: UUID) -> Liquidacion | None: ...

    async def list_by_prestador(self, prestador_id: UUID) -> list[Liquidacion]: ...

    async def create(
        self,
        *,
        prestador_id: UUID,
        numero_liquidacion: str | None,
        periodo: str,
        tipo_liquidacion: str,
        nombre_archivo: str | None,
    ) -> Liquidacion:
        """Genera el `id` (UUID) internamente. `estado`/totales arrancan en sus
        defaults de la tabla (`abierta`, todo en 0) — se actualizan recién al correr
        el motor de reglas."""
        ...

    async def update_estado(self, liquidacion_id: UUID, estado: str) -> None: ...

    async def update_totales(
        self, liquidacion_id: UUID, total_incidentes: int, total_alertas: int, total_importe: float
    ) -> None:
        """Se recalculan después de cada corrida del motor de reglas (import o
        reanalyze) — mismos 3 campos que actualizaba el legacy al final de
        `ejecutar_motor`."""
        ...

    async def delete(self, liquidacion_id: UUID) -> None: ...
