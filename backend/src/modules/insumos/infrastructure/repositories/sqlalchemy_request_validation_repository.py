"""Implementación Postgres (solo lectura) del puerto RequestValidationRepository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.pending_validation import (
    VALIDATION_PENDING,
    PendingValidation,
)
from src.modules.insumos.infrastructure.models.request_validation_model import (
    RequestValidationModel,
)


class SqlAlchemyRequestValidationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_pending(self, hp_request_id: int) -> PendingValidation | None:
        stmt = select(RequestValidationModel).where(
            RequestValidationModel.hp_request_id == hp_request_id,
            RequestValidationModel.status == VALIDATION_PENDING,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        return PendingValidation(
            hp_request_id=row.hp_request_id,
            deadline_at=row.deadline_at,
            initial_percent_left=row.initial_percent_left,
            diagnosis_headline=row.diagnosis_headline,
            diagnosis_detail=row.diagnosis_detail,
        )

    async def get_swap_note(self, hp_request_id: int) -> str | None:
        row = await self._session.get(RequestValidationModel, hp_request_id)
        return row.swap_note if row else None
