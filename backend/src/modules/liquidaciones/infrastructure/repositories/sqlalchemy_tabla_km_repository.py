"""Implementación Postgres del puerto TablaKmRepository (tabla tabla_kms).

Las escrituras parciales viven en `_TablaKmUpdatesMixin` (`tabla_km_updates_mixin.py`),
separadas de esta clase para que ninguna de las dos mitades exceda el límite de
tamaño de clase (ARCHITECTURE_GUIDE.md §4); todas pasan por `_actualizar` con un
`CambiosTablaKm` (ver `tabla_km_cambios.py`): cargar la fila, aplicar los
cambios, flush + refresh y devolver la entidad — o None si la fila no existe."""

import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.infrastructure.models.tabla_km_model import TablaKmModel
from src.modules.liquidaciones.infrastructure.repositories.tabla_km_row_mapper import to_entity
from src.modules.liquidaciones.infrastructure.repositories.tabla_km_updates_mixin import (
    _TablaKmUpdatesMixin,
)


class SqlAlchemyTablaKmRepository(_TablaKmUpdatesMixin):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, tabla_km_id: UUID) -> TablaKm | None:
        row = await self._session.get(TablaKmModel, tabla_km_id)
        return to_entity(row) if row else None

    async def list_by_prestador(self, prestador_id: UUID) -> list[TablaKm]:
        stmt = select(TablaKmModel).where(TablaKmModel.prestador_id == prestador_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [to_entity(row) for row in rows]

    async def list_all(
        self,
        *,
        prestador_id: UUID | None = None,
        q: str | None = None,
    ) -> list[TablaKm]:
        # id como desempate: empresa+sucursal pueden repetirse y sin orden total
        # la paginación Page[T] puede repetir/saltear filas entre páginas.
        stmt = select(TablaKmModel).order_by(
            TablaKmModel.empresa_nombre, TablaKmModel.sucursal_nombre, TablaKmModel.id
        )
        if prestador_id is not None:
            stmt = stmt.where(TablaKmModel.prestador_id == prestador_id)
        if q:
            stmt = stmt.where(_filtro_busqueda(q))
        rows = (await self._session.execute(stmt)).scalars().all()
        return [to_entity(row) for row in rows]

    async def delete(self, tabla_km_id: UUID) -> bool:
        row = await self._session.get(TablaKmModel, tabla_km_id)
        if not row:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True

    async def create(self, **campos: Any) -> TablaKm:
        """La firma tipada (keyword-only, una por columna) vive en el puerto
        `TablaKmRepository`; repetirla acá solo duplicaba la lista de columnas
        — mismo criterio que el fake del puerto."""
        model = TablaKmModel(id=uuid.uuid4(), **campos)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return to_entity(model)


def _filtro_busqueda(q: str) -> ColumnElement[bool]:
    pattern = f"%{q.lower()}%"
    return or_(
        func.lower(TablaKmModel.empresa_nombre).like(pattern),
        func.lower(TablaKmModel.sucursal_nombre).like(pattern),
    )
