"""Caso de uso GetConsumableDetail — port de GET /api/devices/{id}/consumables/{index}/
detail: datos ampliados de un consumible puntual, equivalente a los paneles 'Detalles
de los consumibles' + 'Detalles de rendimiento' del portal HP. A diferencia de
RequestRow (la foto de Insight al momento de la solicitud), lee el estado EN VIVO."""

import asyncio
import logging

from src.modules.insumos.application.dtos.device_detail import ConsumableDetailResult
from src.modules.insumos.application.use_cases._insight_history_range import history_date_range
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway, JsonDict
from src.shared.domain.errors import NotFoundError

logger = logging.getLogger(__name__)


class GetConsumableDetail:
    def __init__(self, insight: InsightGateway) -> None:
        self._insight = insight

    async def execute(self, device_id: int, index: int) -> ConsumableDetailResult:
        """NotFoundError (→ 404) si el consumible no existe en Insight; otros fallos
        de Insight propagan (→ 502)."""
        device, consumables = await asyncio.gather(
            self._insight.get_device_by_id(device_id),
            self._insight.get_device_consumables(device_id),
        )
        consumable = next((c for c in consumables if c.get("index") == index), None)
        if consumable is None:
            raise NotFoundError("Consumible no encontrado en Insight")
        return self._detail_from(device, consumable, await self._engine_cycles(device_id, index))

    async def _engine_cycles(self, device_id: int, index: int) -> int | None:
        """Ciclos de trabajo ACTUALES del equipo: no viene en /consumables (que solo
        trae engineCyclesMonitored, acumulado desde que se instaló ESTE cartucho) — se
        toma del paso más reciente de /consumables/history, que sí trae el contador
        total. Best-effort: sin este dato el panel se muestra igual."""
        try:
            start_date, end_date = history_date_range()
            steps = await self._insight.get_consumable_history(
                device_id, index, start_date=start_date, end_date=end_date
            )
        except Exception as exc:
            logger.error(
                "get_consumable_detail: no se pudieron obtener los ciclos de trabajo "
                "actuales (device %s)",
                device_id,
                exc_info=exc,
            )
            return None
        return steps[0].get("engineCycles") if steps else None  # más reciente primero

    def _detail_from(
        self, device: JsonDict, consumable: JsonDict, engine_cycles: int | None
    ) -> ConsumableDetailResult:
        extended = device.get("extendedFields") or {}
        reorder = consumable.get("reorderPart") or {}
        return ConsumableDetailResult(
            model=extended.get("mibDescription") or extended.get("model"),
            type=consumable.get("type"),
            colour=consumable.get("colour"),
            serial_number=consumable.get("serialNumber") or None,
            sku=consumable.get("sku"),
            adjusted_yield=consumable.get("yield") or None,
            reorder_sku=reorder.get("sku"),
            reorder_yield=reorder.get("yield") or None,
            capacity=consumable.get("maxLevel"),
            percent_left=consumable.get("percentLeft"),
            days_left=consumable.get("daysLeft"),
            pages_left=consumable.get("pagesLeft"),
            last_read=consumable.get("lastRead"),
            engine_cycles=engine_cycles,
            first_read=consumable.get("firstRead"),
            days_monitored=consumable.get("daysMonitored"),
            engine_cycles_monitored=consumable.get("engineCyclesMonitored"),
        )
