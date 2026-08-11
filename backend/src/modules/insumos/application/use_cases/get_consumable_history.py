"""Caso de uso GetConsumableHistory — port de GET /api/devices/{id}/consumables/{index}/
history: historial de nivel de UN consumible puntual, alimenta el gráfico del modal de
detalle (mismo dato que la 'Historial del nivel de consumibles' del portal HP, que no se
puede embeber/linkear directo). Pide el rango máximo que permite Insight (~12 meses)
para que el gráfico cubra un período comparable al del portal, no solo los 90 días que
trae por default."""

from src.modules.insumos.application.dtos.device_detail import ConsumableHistoryPoint
from src.modules.insumos.application.use_cases._insight_history_range import history_date_range
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway


class GetConsumableHistory:
    def __init__(self, insight: InsightGateway) -> None:
        self._insight = insight

    async def execute(self, device_id: int, index: int) -> list[ConsumableHistoryPoint]:
        """Puntos en orden cronológico (Insight los devuelve más reciente primero).
        Un fallo de Insight propaga (ExternalServiceError → 502) — sin historial no
        hay gráfico que dibujar."""
        start_date, end_date = history_date_range()
        steps = await self._insight.get_consumable_history(
            device_id, index, start_date=start_date, end_date=end_date
        )
        return [
            ConsumableHistoryPoint(date=str(step["recordDate"]), level=step.get("level"))
            for step in reversed(steps)
            if step.get("recordDate")
        ]
