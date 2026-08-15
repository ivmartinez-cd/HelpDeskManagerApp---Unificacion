"""Puerto: telemetría de dispositivos por serial."""

from typing import Protocol
from uuid import UUID

from src.modules.analisis_log_hp.domain.entities.saved_analysis import TelemetryEvent


class TelemetryRepository(Protocol):
    async def add_events(self, events: list[TelemetryEvent]) -> None: ...

    async def get_events_by_serial(self, serial: str) -> list[TelemetryEvent]: ...

    async def delete_by_analysis_id(self, analysis_id: UUID) -> int: ...
