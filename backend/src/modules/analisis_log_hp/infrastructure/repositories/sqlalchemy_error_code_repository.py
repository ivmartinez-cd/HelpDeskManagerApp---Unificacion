"""Repositorio SQLAlchemy del catálogo de códigos de error HP.

Semántica upsert COALESCE/NULLIF: campo vacío/nulo nunca pisa un valor
existente (§5.4 caracterización). Idéntico al upsert del legacy.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import Insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analisis_log_hp.domain.entities.error_code import ErrorCode
from src.modules.analisis_log_hp.infrastructure.models.error_code_model import ErrorCodeModel
from src.shared.presentation.schemas.pagination import Page


class SqlAlchemyErrorCodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_code(self, code: str) -> ErrorCode | None:
        row = (
            await self._session.execute(
                select(ErrorCodeModel).where(ErrorCodeModel.code == code)
            )
        ).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def get_by_codes(self, codes: list[str]) -> dict[str, ErrorCode]:
        if not codes:
            return {}
        rows = (
            await self._session.execute(
                select(ErrorCodeModel).where(ErrorCodeModel.code.in_(codes))
            )
        ).scalars().all()
        return {row.code: _to_entity(row) for row in rows}

    async def upsert(
        self,
        code: str,
        *,
        severity: str | None = None,
        description: str | None = None,
        solution_url: str | None = None,
        solution_content: str | None = None,
    ) -> ErrorCode:
        stmt = pg_insert(ErrorCodeModel).values(
            code=code,
            severity=severity,
            description=description,
            solution_url=solution_url,
            solution_content=solution_content,
        )
        # Vacío nunca pisa: COALESCE(NULLIF(excluded.campo, ''), existente)
        returning_stmt = stmt.on_conflict_do_update(
            index_elements=["code"],
            set_={
                "severity": func.coalesce(
                    func.nullif(stmt.excluded.severity, ""), ErrorCodeModel.severity
                ),
                "description": func.coalesce(
                    func.nullif(stmt.excluded.description, ""), ErrorCodeModel.description
                ),
                "solution_url": func.coalesce(
                    func.nullif(stmt.excluded.solution_url, ""), ErrorCodeModel.solution_url
                ),
                "solution_content": func.coalesce(
                    func.nullif(stmt.excluded.solution_content, ""), ErrorCodeModel.solution_content
                ),
                "updated_at": func.now(),
            },
        ).returning(ErrorCodeModel)
        row = (await self._session.execute(returning_stmt)).scalar_one()
        await self._session.flush()
        return _to_entity(row)

    async def list_page(self, page: int, size: int) -> Page[ErrorCode]:
        total_res = await self._session.execute(
            select(func.count()).select_from(ErrorCodeModel)
        )
        total = total_res.scalar_one()
        rows = (
            await self._session.execute(
                select(ErrorCodeModel)
                .order_by(ErrorCodeModel.code)
                .limit(size)
                .offset((page - 1) * size)
            )
        ).scalars().all()
        return Page(items=[_to_entity(r) for r in rows], total=total, page=page, size=size)

    async def bulk_update_solution_urls(self, updates: dict[str, dict[str, Any]]) -> int:
        """Actualiza URLs de ayuda y descripción para múltiples códigos a la vez.

        `updates` = {code: {'url': str, 'description': str}}. Solo pisa si el
        valor nuevo no es vacío (misma semántica COALESCE/NULLIF).
        """
        count = 0
        for code, data in updates.items():
            url = data.get("url") or None
            desc = data.get("description") or None
            if not url and not desc:
                continue
            await self._session.execute(_solution_url_upsert_stmt(code, url, desc))
            count += 1
        if count:
            await self._session.flush()
        return count


def _solution_url_upsert_stmt(code: str, url: str | None, desc: str | None) -> Insert:
    """INSERT ... ON CONFLICT que solo pisa solution_url/description si vienen no vacíos."""
    stmt = pg_insert(ErrorCodeModel).values(code=code, solution_url=url, description=desc)
    return stmt.on_conflict_do_update(
        index_elements=["code"],
        set_={
            "solution_url": func.coalesce(
                func.nullif(stmt.excluded.solution_url, ""), ErrorCodeModel.solution_url
            ),
            "description": func.coalesce(
                func.nullif(stmt.excluded.description, ""), ErrorCodeModel.description
            ),
            "updated_at": func.now(),
        },
    )


def _to_entity(row: ErrorCodeModel) -> ErrorCode:
    return ErrorCode(
        code=row.code,
        severity=row.severity,
        description=row.description,
        solution_url=row.solution_url,
        solution_content=row.solution_content,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
