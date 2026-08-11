"""Implementación Postgres del puerto RequestValidationRepository."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import CursorResult, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.pending_validation import (
    VALIDATION_PENDING,
    PendingValidation,
    PendingValidationWork,
    ValidationStart,
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
        return _to_pending(row) if row else None

    async def get_pending_batch(
        self, hp_request_ids: Sequence[int]
    ) -> dict[int, PendingValidation]:
        if not hp_request_ids:
            return {}
        stmt = select(RequestValidationModel).where(
            RequestValidationModel.hp_request_id.in_(hp_request_ids),
            RequestValidationModel.status == VALIDATION_PENDING,
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return {row.hp_request_id: _to_pending(row) for row in rows}

    async def get_swap_note(self, hp_request_id: int) -> str | None:
        row = await self._session.get(RequestValidationModel, hp_request_id)
        return row.swap_note if row else None

    async def get_pending_ids(self, hp_request_ids: Sequence[int]) -> set[int]:
        if not hp_request_ids:
            return set()
        stmt = select(RequestValidationModel.hp_request_id).where(
            RequestValidationModel.hp_request_id.in_(hp_request_ids),
            RequestValidationModel.status == VALIDATION_PENDING,
        )
        return set((await self._session.execute(stmt)).scalars().all())

    async def is_diagnosed(self, hp_request_id: int) -> bool:
        stmt = select(RequestValidationModel.swap_checked).where(
            RequestValidationModel.hp_request_id == hp_request_id
        )
        return bool((await self._session.execute(stmt)).scalar_one_or_none())

    async def start(self, data: ValidationStart) -> None:
        """UPSERT idéntico al legacy: si la fila ya existe, solo completa swap_note/
        diagnosis_* (y swap_checked) sin reiniciar el reloj ni pisar el status, y solo
        si todavía no se había diagnosticado."""
        now = datetime.now(UTC)
        stmt = pg_insert(RequestValidationModel).values(
            hp_request_id=data.hp_request_id,
            customer_id=data.customer_id,
            device_id=data.device_id,
            device_serial=data.device_serial,
            sku=data.sku,
            initial_percent_left=data.initial_percent_left,
            detected_at=now,
            deadline_at=now + timedelta(minutes=data.deadline_minutes),
            status=VALIDATION_PENDING,
            swap_note=data.swap_note,
            swap_checked=True,
            diagnosis_headline=data.diagnosis_headline,
            diagnosis_detail=data.diagnosis_detail,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[RequestValidationModel.hp_request_id],
            set_={
                "swap_note": stmt.excluded.swap_note,
                "swap_checked": True,
                "diagnosis_headline": stmt.excluded.diagnosis_headline,
                "diagnosis_detail": stmt.excluded.diagnosis_detail,
            },
            where=RequestValidationModel.swap_checked.is_(False),
        )
        await self._session.execute(stmt)

    async def resolve(self, hp_request_id: int, status: str) -> bool:
        stmt = (
            update(RequestValidationModel)
            .where(
                RequestValidationModel.hp_request_id == hp_request_id,
                RequestValidationModel.status == VALIDATION_PENDING,
            )
            .values(status=status, resolved_at=func.now())
        )
        result = cast(CursorResult[Any], await self._session.execute(stmt))
        return result.rowcount > 0

    async def get_all_pending(self) -> list[PendingValidationWork]:
        is_due = (RequestValidationModel.deadline_at <= func.now()).label("is_due")
        stmt = select(RequestValidationModel, is_due).where(
            RequestValidationModel.status == VALIDATION_PENDING
        )
        rows = (await self._session.execute(stmt)).all()
        return [_to_work(model, due) for model, due in rows]


def _to_pending(row: RequestValidationModel) -> PendingValidation:
    return PendingValidation(
        hp_request_id=row.hp_request_id,
        deadline_at=row.deadline_at,
        initial_percent_left=row.initial_percent_left,
        diagnosis_headline=row.diagnosis_headline,
        diagnosis_detail=row.diagnosis_detail,
        swap_note=row.swap_note,
    )


def _to_work(row: RequestValidationModel, is_due: bool) -> PendingValidationWork:
    return PendingValidationWork(
        hp_request_id=row.hp_request_id,
        customer_id=row.customer_id,
        device_id=row.device_id,
        device_serial=row.device_serial,
        sku=row.sku,
        initial_percent_left=row.initial_percent_left,
        is_due=is_due,
    )
