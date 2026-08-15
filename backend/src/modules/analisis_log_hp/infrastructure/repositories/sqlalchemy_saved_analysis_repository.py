from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analisis_log_hp.domain.entities.saved_analysis import SavedAnalysis
from src.modules.analisis_log_hp.infrastructure.models.saved_analysis_model import (
    SavedAnalysisModel,
)
from src.shared.presentation.schemas.pagination import Page


class SqlAlchemySavedAnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        name: str,
        equipment_identifier: str | None,
        incidents: list[dict[str, Any]],
        global_severity: str,
        ai_diagnosis: str | None = None,
    ) -> SavedAnalysis:
        row = SavedAnalysisModel(
            name=name,
            equipment_identifier=equipment_identifier,
            incidents=incidents,
            global_severity=global_severity,
            ai_diagnosis=ai_diagnosis,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def get_by_id(self, id: uuid.UUID) -> SavedAnalysis | None:
        row = (
            await self._session.execute(
                select(SavedAnalysisModel).where(SavedAnalysisModel.id == id)
            )
        ).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def list_page(self, page: int, size: int) -> Page[SavedAnalysis]:
        total = (
            await self._session.execute(
                select(func.count()).select_from(SavedAnalysisModel)
            )
        ).scalar_one()
        rows = (
            await self._session.execute(
                select(SavedAnalysisModel)
                .order_by(SavedAnalysisModel.created_at.desc())
                .limit(size)
                .offset((page - 1) * size)
            )
        ).scalars().all()
        return Page(items=[_to_entity(r) for r in rows], total=total, page=page, size=size)

    async def update(
        self,
        id: uuid.UUID,
        incidents: list[dict[str, Any]],
        global_severity: str,
        ai_diagnosis: str | None = None,
    ) -> SavedAnalysis | None:
        row = (
            await self._session.execute(
                select(SavedAnalysisModel).where(SavedAnalysisModel.id == id)
            )
        ).scalar_one_or_none()
        if not row:
            return None
        row.incidents = incidents
        row.global_severity = global_severity
        if ai_diagnosis is not None:
            row.ai_diagnosis = ai_diagnosis
        await self._session.flush()
        return _to_entity(row)

    async def delete(self, id: uuid.UUID) -> bool:
        row = (
            await self._session.execute(
                select(SavedAnalysisModel).where(SavedAnalysisModel.id == id)
            )
        ).scalar_one_or_none()
        if not row:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True


def _to_entity(row: SavedAnalysisModel) -> SavedAnalysis:
    return SavedAnalysis(
        id=row.id,
        name=row.name,
        equipment_identifier=row.equipment_identifier,
        incidents=row.incidents or [],
        global_severity=row.global_severity,
        ai_diagnosis=row.ai_diagnosis,
        created_at=row.created_at,
    )
