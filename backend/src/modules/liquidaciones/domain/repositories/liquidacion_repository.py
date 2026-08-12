"""Puerto de preliquidaciones importadas (liquidaciones)."""

from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion


class LiquidacionRepository(Protocol):
    async def get_by_id(self, liquidacion_id: UUID) -> Liquidacion | None: ...

    async def list_by_prestador(self, prestador_id: UUID) -> list[Liquidacion]: ...

    async def list_all(self) -> list[Liquidacion]:
        """Todas las liquidaciones ordenadas por fecha_importacion desc — para la
        vista global del dashboard y del listado sin filtro de prestador."""
        ...

    async def create(
        self,
        *,
        prestador_id: UUID,
        numero_liquidacion: str | None,
        periodo: str,
        tipo_liquidacion: str,
        nombre_archivo: str | None,
        total_incidentes: int,
        total_importe: float,
    ) -> Liquidacion:
        """Genera el `id` (UUID) internamente. `estado` arranca en su default
        (`abierta`) — `total_incidentes`/`total_importe` los pasa el caller porque ya
        se conocen del parseo del archivo (no hace falta un segundo `UPDATE` después
        de insertar los incidentes, a diferencia del legacy). `total_alertas` arranca
        en 0 — lo fija recién `update_total_alertas` al correr el motor de reglas."""
        ...

    async def update_estado(self, liquidacion_id: UUID, estado: str) -> None: ...

    async def update_total_alertas(self, liquidacion_id: UUID, total_alertas: int) -> None:
        """El único campo que `ejecutar_motor` del legacy tocaba al final de una
        corrida (import o reanalyze) — `total_incidentes`/`total_importe` se fijan al
        importar y no se recalculan acá, confirmado leyendo `motor_reglas.py` y el
        router `POST /liquidaciones/{id}/reanalize` (wrapper fino, sin otros efectos:
        no toca `estado` ni el resto de los totales)."""
        ...

    async def delete(self, liquidacion_id: UUID) -> bool: ...
