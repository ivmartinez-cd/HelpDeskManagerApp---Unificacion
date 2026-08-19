"""Repositorio SQLAlchemy del catálogo de manuales CPMD.

Matching por keyword hecho en Python (no SQL): el catálogo es chico —
decenas de manuales, no miles— y el criterio del legacy es sustring
case-insensitive por keyword, más simple de leer así que con
`unnest()` + `ILIKE` en SQL.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analisis_log_hp.domain.entities.cpmd_manual import CpmdManual
from src.modules.analisis_log_hp.infrastructure.models.cpmd_manual_model import CpmdManualModel


class SqlAlchemyCpmdManualRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_model_family(self, model_family: str) -> CpmdManual | None:
        target = model_family.upper()
        rows = (await self._session.execute(select(CpmdManualModel))).scalars().all()
        for row in rows:
            if any(kw.upper() in target for kw in row.keywords):
                return _to_entity(row)
        return None

    async def get_by_id(self, manual_id: int) -> CpmdManual | None:
        row = await self._session.get(CpmdManualModel, manual_id)
        return _to_entity(row) if row else None

    async def create(self, *, keywords: list[str], label: str, filename: str) -> CpmdManual:
        row = CpmdManualModel(keywords=keywords, label=label, filename=filename)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)


def _to_entity(row: CpmdManualModel) -> CpmdManual:
    return CpmdManual(
        id=row.id,
        keywords=row.keywords,
        label=row.label,
        filename=row.filename,
        uploaded_at=row.uploaded_at,
    )
