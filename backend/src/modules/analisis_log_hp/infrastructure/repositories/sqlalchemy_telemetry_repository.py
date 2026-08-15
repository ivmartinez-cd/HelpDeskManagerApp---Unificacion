from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analisis_log_hp.domain.entities.saved_analysis import TelemetryEvent
from src.modules.analisis_log_hp.infrastructure.models.telemetry_model import TelemetryModel


class SqlAlchemyTelemetryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_events(self, events: list[TelemetryEvent]) -> None:
        if not events:
            return
        for evt in events:
            self._session.add(
                TelemetryModel(
                    device_serial=evt.device_serial,
                    saved_analysis_id=evt.saved_analysis_id,
                    code=evt.code,
                    classification=evt.classification,
                    severity=evt.severity,
                    occurrences=evt.occurrences,
                    counter=evt.counter,
                    event_time=evt.event_time,
                )
            )
        await self._session.flush()

    async def get_events_by_serial(self, serial: str) -> list[TelemetryEvent]:
        rows = (
            await self._session.execute(
                select(TelemetryModel)
                .where(TelemetryModel.device_serial == serial)
                .order_by(TelemetryModel.event_time.asc())
            )
        ).scalars().all()
        return [_to_entity(r) for r in rows]

    async def delete_by_analysis_id(self, analysis_id: uuid.UUID) -> int:
        from sqlalchemy.engine import CursorResult

        result: CursorResult[tuple[()]] = await self._session.execute(  # type: ignore[assignment]
            delete(TelemetryModel).where(
                TelemetryModel.saved_analysis_id == analysis_id
            )
        )
        return int(result.rowcount)


def _to_entity(row: TelemetryModel) -> TelemetryEvent:
    return TelemetryEvent(
        device_serial=row.device_serial,
        saved_analysis_id=row.saved_analysis_id,
        code=row.code,
        classification=row.classification,
        severity=row.severity,
        occurrences=row.occurrences,
        counter=row.counter,
        event_time=row.event_time,
    )
