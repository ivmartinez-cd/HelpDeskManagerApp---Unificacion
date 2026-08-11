"""Puerto de las agregaciones históricas sobre order_audit (las Estadísticas).

Separado de OrderAuditRepository a propósito: aquel es el puerto de escritura + el
listado del Historial (una fila = un evento), este devuelve SOLO agregados de lectura.
Todos los métodos filtran `dry_run = false` y acotan por día calendario argentino
(equivalente del `date(created_at, 'localtime')` del legacy) — el "día" de negocio
nunca es el día UTC del servidor.
"""

from datetime import date
from typing import Protocol

from src.modules.insumos.domain.value_objects.audit_statistics import (
    CustomerActivity,
    DailyEventCount,
    DeviceCount,
    DispatchRow,
    FailureReasonCount,
    FulfillmentRow,
    RecentFailure,
    SkuCount,
    SourceSplit,
)


class AuditStatisticsRepository(Protocol):
    async def earliest_day(self) -> date | None:
        """Primer día con actividad registrada — el frontend lo usa para no ofrecer
        rangos anteriores a que la app existiera. None si no hay historial."""
        ...

    async def customer_name(self, customer_id: int) -> str | None:
        """Último nombre visto para ese cliente en order_audit, sin acotar por rango.
        Fallback cuando el cliente ya no está en el padrón (se podó) pero todavía
        tiene historial."""
        ...

    async def daily_counts(
        self, start: date, end: date, *, customer_id: int | None = None
    ) -> list[DailyEventCount]:
        """CREATED/FAILED por día. Solo los días CON eventos: completar los huecos con
        ceros es responsabilidad del dominio (fill_daily_series)."""
        ...

    async def event_totals(
        self, start: date, end: date, *, customer_id: int | None = None
    ) -> dict[str, int]:
        """{evento: total} en el rango — se pide dos veces por request (período actual
        y anterior) para la comparativa."""
        ...

    async def customer_activity(self, start: date, end: date) -> list[CustomerActivity]:
        """Ranking completo de clientes por actividad (created+failed), más activo
        primero. Completo y no top-N: el total de clientes activos sale de su largo."""
        ...

    async def top_skus(
        self, start: date, end: date, *, customer_id: int | None = None
    ) -> list[SkuCount]:
        """Ranking completo de SKUs pedidos (solo CREATED), más pedido primero — el
        conteo de SKUs distintos sale de su largo."""
        ...

    async def top_devices(
        self, start: date, end: date, customer_id: int, limit: int
    ) -> list[DeviceCount]:
        """Equipos que más pedidos generaron para el cliente."""
        ...

    async def failure_reasons(
        self, start: date, end: date, customer_id: int, limit: int
    ) -> list[FailureReasonCount]:
        """Motivos de fallo agrupados por `detail`, más frecuente primero."""
        ...

    async def recent_failures(
        self, start: date, end: date, customer_id: int, limit: int
    ) -> list[RecentFailure]:
        """Últimos fallos del cliente, más reciente primero."""
        ...

    async def source_split(self, start: date, end: date, customer_id: int) -> SourceSplit:
        """Auto-cargados vs. total. El detalle de auto-carga tiene variantes ("…—
        Auto-carga"), por eso se detecta por subcadena y no por igualdad exacta."""
        ...

    async def fulfillment_rows(
        self, start: date, end: date, customer_id: int
    ) -> list[FulfillmentRow]:
        """CREATED con hp_request_time presente. Los anteriores a que se capturara esa
        columna quedan afuera del universo medible, no se los cuenta como 0."""
        ...

    async def dispatch_rows(
        self, start: date, end: date, customer_id: int
    ) -> list[DispatchRow]:
        """CREATED de insumo (no incidentes) con pedido real en CD — excluye dry-runs
        por prefijo además del flag, porque el ID sintético no resuelve a un supply."""
        ...
