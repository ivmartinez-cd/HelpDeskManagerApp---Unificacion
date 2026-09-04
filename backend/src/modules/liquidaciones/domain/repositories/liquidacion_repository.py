"""Puerto de preliquidaciones importadas (liquidaciones)."""

from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion


class LiquidacionRepository(Protocol):
    async def get_by_id(self, liquidacion_id: UUID) -> Liquidacion | None: ...

    async def list_filtered(
        self,
        prestador_id: UUID | None = None,
        estado: str | None = None,
        periodo: str | None = None,
        anio: int | None = None,
    ) -> list[Liquidacion]:
        """Todas las liquidaciones que cumplan los filtros opcionales, ordenadas
        por fecha_importacion desc.  Sin filtro = devuelve todas. `anio` filtra
        por el año de `periodo` (YYYY-MM); si se pasa junto con `periodo`, este
        último ya lo implica y ambos deben ser consistentes."""
        ...

    async def list_numeros_liquidacion(self) -> set[str]:
        """Conjunto de todos los `numero_liquidacion` no-nulos en la DB.
        Usado por el sync de CD para detectar novedades sin cargar filas completas."""
        ...

    async def list_activas_por_prestador_con_numero(
        self, prestador_id: UUID, estados: frozenset[str]
    ) -> list[Liquidacion]:
        """Liquidaciones del prestador que tienen `numero_liquidacion` (vínculo AyC)
        y están en alguno de los `estados` dados. Usado por el sync para cruzar contra
        la lista de AyC y detectar las que fueron anuladas allá sin pasar por nuestra app."""
        ...

    async def list_periodos(self) -> list[str]:
        """Valores distintos de `periodo` (YYYY-MM) en orden descendente."""
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

    async def update_estado(self, liquidacion_id: UUID, estado: str) -> Liquidacion | None: ...

    async def update_extra(
        self,
        liquidacion_id: UUID,
        concepto_extra: str | None,
        monto_extra: float | None,
    ) -> Liquidacion | None: ...

    async def update_numero_factura(
        self, liquidacion_id: UUID, numero_factura: str, factura_pdf_url: str | None
    ) -> Liquidacion | None:
        """Solo lo escribe la reconciliación contra AyC (`FacturaLocal`-`FacturaNro`
        de `getLiquidationById`) — a diferencia de `update_extra`, no hay carga
        manual: sin PATCH de usuario para este campo. `factura_pdf_url` viaja junto
        porque se deriva del mismo `getLiquidationById` (ver
        `domain/services/factura_pdf_url.py`); `None` si AyC no trae `Fecha`/
        `RsPrestador` para reconstruirlo."""
        ...

    async def update_total_alertas(self, liquidacion_id: UUID, total_alertas: int) -> None:
        """El único campo que `ejecutar_motor` del legacy tocaba al final de una
        corrida (import o reanalyze) — `total_incidentes`/`total_importe` se fijan al
        importar y no se recalculan acá, confirmado leyendo `motor_reglas.py` y el
        router `POST /liquidaciones/{id}/reanalize` (wrapper fino, sin otros efectos:
        no toca `estado` ni el resto de los totales)."""
        ...

    async def update_totales(
        self, liquidacion_id: UUID, total_incidentes: int, total_importe: float
    ) -> None:
        """Recalculo tras `reconciliar_incidentes` — el caller pasa lo que quedó
        realmente persistido (no lo que reportó AyC crudo), para que la DB y el
        total cuenten la misma historia si `update_cobrados`/`delete_by_ids`
        fallara a mitad de camino."""
        ...

    async def update_periodo(self, liquidacion_id: UUID, periodo: str) -> None:
        """`periodo` se fija al crear la liquidación (moda de `fecha_cierre` de sus
        incidentes en ese momento, o un fallback por fecha de emisión si ninguno
        había cerrado todavía) y sin esto quedaba congelado para siempre: si los
        incidentes cerraban después con fechas de otro mes, la reconciliación
        actualizaba incidentes/importe pero no el período. Solo lo llama
        `ReconciliarLiquidacion` cuando el recálculo da un valor distinto y no
        vacío."""
        ...

    async def count_pendientes_por_prestador(self) -> list[tuple[str, int]]:
        """Conteo de liquidaciones pendientes (excluye aprobada y cerrada) agrupado
        por prestador. Retorna pares (nombre_corto, count) ordenados por count desc."""
        ...

    async def delete(self, liquidacion_id: UUID) -> bool: ...
