"""Implementación Postgres del puerto ReglaAlertaRepository (tabla reglas_alerta)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.regla_alerta import (
    CONFIG_GENERA_OBSERVACIONES,
    ReglaAlerta,
)
from src.modules.liquidaciones.infrastructure.models.regla_alerta_model import ReglaAlertaModel


class SqlAlchemyReglaAlertaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_activas(self) -> dict[str, ReglaAlerta]:
        stmt = select(ReglaAlertaModel).where(ReglaAlertaModel.activa.is_(True))
        rows = (await self._session.execute(stmt)).scalars().all()
        return {row.codigo: _to_entity(row) for row in rows}

    async def list_all(self) -> list[ReglaAlerta]:
        stmt = select(ReglaAlertaModel).order_by(ReglaAlertaModel.codigo)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def set_activa(self, codigo: str, activa: bool) -> ReglaAlerta | None:
        stmt = select(ReglaAlertaModel).where(ReglaAlertaModel.codigo == codigo)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        row.activa = activa
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def set_genera_observaciones(self, codigo: str, valor: bool) -> ReglaAlerta | None:
        stmt = select(ReglaAlertaModel).where(ReglaAlertaModel.codigo == codigo)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        # Reasigna un dict nuevo (no mutar in-place): JSONB sin `MutableDict`
        # no detecta cambios sobre el objeto existente.
        row.configuracion = {**row.configuracion, CONFIG_GENERA_OBSERVACIONES: valor}
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)


def _to_entity(row: ReglaAlertaModel) -> ReglaAlerta:
    return ReglaAlerta(
        id=row.id,
        codigo=row.codigo,
        nombre=row.nombre,
        descripcion=row.descripcion,
        activa=row.activa,
        riesgo_base=row.riesgo_base,
        configuracion=row.configuracion,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
