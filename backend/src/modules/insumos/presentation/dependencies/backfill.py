"""Factory del backfill de consumable_serial (chequeo periódico del poller + script
manual, ver application/use_cases/backfill_consumable_serial.py)."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.use_cases.backfill_consumable_serial import (
    BackfillConsumableSerial,
    BackfillConsumableSerialPorts,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_processed_request_repository import (  # noqa: E501
    SqlAlchemyProcessedRequestRepository,
)
from src.modules.insumos.presentation.wiring import get_insight_gateway


def build_backfill_consumable_serial(session: AsyncSession) -> BackfillConsumableSerial:
    ports = BackfillConsumableSerialPorts(
        insight=get_insight_gateway(),
        processed=SqlAlchemyProcessedRequestRepository(session),
    )
    return BackfillConsumableSerial(ports)
