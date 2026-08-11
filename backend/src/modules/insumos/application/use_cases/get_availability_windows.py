"""Caso de uso GetAvailabilityWindows — port de GET /api/devices/{id}/availability-
windows: ventanas de "sin contacto" del EQUIPO (no de un consumible puntual), alimenta
la franja que el modal de detalle dibuja sobre el gráfico de nivel, igual que el portal
HP (ver availability_windows.py: se deriva de las alertas AVAILABILITY, Insight no
tiene un endpoint de historial de conectividad dedicado)."""

from src.modules.insumos.application.use_cases._insight_history_range import (
    history_datetime_range,
)
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway
from src.modules.insumos.domain.services.availability_windows import (
    AvailabilityWindow,
    build_availability_windows,
)

_MAX_ALERTS = 500


class GetAvailabilityWindows:
    def __init__(self, insight: InsightGateway) -> None:
        self._insight = insight

    async def execute(self, device_id: int) -> list[AvailabilityWindow]:
        """Un fallo de Insight propaga (→ 502) — sin alertas no hay franja que armar."""
        from_date, to_date = history_datetime_range()
        alerts = await self._insight.get_device_alerts_history(
            device_id,
            alert_classes=["AVAILABILITY"],
            from_date=from_date,
            to_date=to_date,
            max_results=_MAX_ALERTS,
        )
        return build_availability_windows(alerts)
