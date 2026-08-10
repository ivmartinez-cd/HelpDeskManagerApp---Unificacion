"""Puerto de dominio para la Insight Portal API (HP SDS Manager LATAM).

Port de InsightApiClient del legacy. Las respuestas son los dicts crudos de Insight
(claves camelCase del wire) — las entidades de dominio se modelan recién donde un caso
de uso las consume, no acá. La implementación concreta vive en
infrastructure/insight/httpx_insight_gateway.py.

Trampa de fechas (caracterización §7): NO todos los campos de fecha de Insight son UTC.
`requested`/`statusDate`/`replacedDate` (consumable-requests) y `recordDate`
(consumables/history) son UTC verificado; `readDateLocal` tiene convención horaria NO
confirmada y ya causó dos conclusiones erróneas retractadas — clasificar cada campo
nuevo explícitamente antes de usarlo.
"""

from typing import Any, Protocol

JsonDict = dict[str, Any]


class InsightGateway(Protocol):
    async def ping(self) -> None:
        """Verifica credenciales obteniendo/renovando el token."""
        ...

    async def get_customers(self) -> list[JsonDict]: ...

    async def get_devices(self, customer_id: int) -> list[JsonDict]: ...

    async def get_zones(self, customer_id: int) -> list[JsonDict]: ...

    async def get_monitors(self, customer_id: int) -> list[JsonDict]:
        """Colectores (DCA) del cliente con su estado real (`online`/`status`) — para
        distinguir un colector caído (todos sus equipos dejan de reportar) de retiros
        físicos reales. `online` no es confiable solo: exigir también `status='ACTIVE'`
        y `last_contact` vencido (caracterización §6.1)."""
        ...

    async def get_device_by_id(self, device_id: int) -> JsonDict: ...

    async def get_device_consumables(self, device_id: int) -> list[JsonDict]:
        """Estado EN VIVO de los consumibles — a diferencia de `consumable.percentLeft`
        en get_consumable_requests, que es la foto del momento de la solicitud y puede
        haber quedado vieja (caso real MXBCQ7C03T, ago-2026; base de la ventana de
        validación 0%)."""
        ...

    async def get_consumable_history(
        self,
        device_id: int,
        consumable_index: int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[JsonDict]:
        """Historial de lecturas de UN consumible, más reciente primero. Cada paso trae
        `consumableSerial` (chip físico): distingue cartucho reemplazado (serie distinta)
        de falla de sensor (misma serie, salto imposible). Sin start_date Insight
        devuelve solo 90 días; start_date acepta como máximo 12 meses atrás (más viejo
        → 400; el legacy usa 364 días, no 365)."""
        ...

    async def get_consumable_requests(
        self,
        customer_id: int,
        workflow_status: str = "OUTSTANDING",
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[JsonDict]:
        """Solicitudes de consumibles. from/to_date en el formato exacto de
        today_range_utc ("%Y-%m-%dT%H:%M:%SZ", Z literal) — no cualquier ISO 8601."""
        ...

    async def update_consumable_request(
        self,
        request_id: int,
        external_ref: str | None = None,
        status_update: str | None = None,
        comment: str | None = None,
    ) -> JsonDict:
        """PATCH de una solicitud. `status_update` válidos: ACTION, DELAYED, DELIVERED,
        DISPATCHED, DELETE, REJECTED, QUERY, IGNORE, UNIGNORE — nótese ACTION, no
        ACTIONED (bug corregido documentado en el CHANGELOG legacy [1.0.0])."""
        ...

    async def get_device_alerts_history(
        self,
        device_id: int,
        alert_classes: list[str] | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        max_results: int | None = None,
    ) -> list[JsonDict]:
        """Alertas históricas del equipo. Con alertClasses=["AVAILABILITY"] son los
        eventos de conectividad del equipo — la fuente real de la franja "sin contacto"
        del portal HP (no hay endpoint dedicado de conectividad)."""
        ...
