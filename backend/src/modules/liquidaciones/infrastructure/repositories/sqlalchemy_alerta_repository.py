"""Implementación Postgres del puerto AlertaRepository (tabla alertas)."""

import uuid
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.alerta import Alerta
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import AlertaGenerada
from src.modules.liquidaciones.infrastructure.models.alerta_model import AlertaModel


class SqlAlchemyAlertaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[Alerta]:
        stmt = select(AlertaModel).where(AlertaModel.liquidacion_id == liquidacion_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def replace_for_liquidacion(
        self, liquidacion_id: UUID, alertas: Sequence[AlertaGenerada]
    ) -> list[Alerta]:
        await self._session.execute(
            delete(AlertaModel).where(AlertaModel.liquidacion_id == liquidacion_id)
        )
        modelos = [_a_model(liquidacion_id, a) for a in alertas]
        self._session.add_all(modelos)
        await self._session.flush()
        for modelo in modelos:
            await self._session.refresh(modelo)
        return [_to_entity(m) for m in modelos]


def _a_model(liquidacion_id: UUID, alerta: AlertaGenerada) -> AlertaModel:
    return AlertaModel(
        id=uuid.uuid4(),
        incidente_id=alerta.incidente_id,
        liquidacion_id=liquidacion_id,
        tipo_alerta=alerta.tipo_alerta,
        descripcion=alerta.descripcion,
        datos_contexto=alerta.datos_contexto,
        riesgo=alerta.riesgo,
    )


def _to_entity(row: AlertaModel) -> Alerta:
    return Alerta(
        id=row.id,
        incidente_id=row.incidente_id,
        liquidacion_id=row.liquidacion_id,
        tipo_alerta=row.tipo_alerta,
        descripcion=row.descripcion,
        datos_contexto=row.datos_contexto,
        riesgo=row.riesgo,
        estado=row.estado,
        fecha_generacion=row.fecha_generacion,
    )
