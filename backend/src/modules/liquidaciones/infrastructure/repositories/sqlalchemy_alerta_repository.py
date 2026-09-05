"""Implementación Postgres del puerto AlertaRepository (tablas alertas /
alerta_incidentes — esta última solo para alertas agrupadas, `es_grupo=True`,
ex `Observacion`)."""

import uuid
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.alerta import (
    ROL_PRINCIPAL,
    ROL_REFERENCIA,
    Alerta,
)
from src.modules.liquidaciones.domain.services.conciliar_alertas import AlertaConciliada
from src.modules.liquidaciones.infrastructure.models.alerta_model import (
    AlertaIncidenteModel,
    AlertaModel,
)


class SqlAlchemyAlertaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[Alerta]:
        stmt = select(AlertaModel).where(AlertaModel.liquidacion_id == liquidacion_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        grupos = await self._grupo_incidente_ids([r.id for r in rows if r.es_grupo])
        return [_to_entity(row, grupos.get(row.id, ())) for row in rows]

    async def _grupo_incidente_ids(
        self, alerta_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[uuid.UUID, ...]]:
        if not alerta_ids:
            return {}
        stmt = select(AlertaIncidenteModel).where(AlertaIncidenteModel.alerta_id.in_(alerta_ids))
        vinculos = (await self._session.execute(stmt)).scalars().all()
        por_alerta: dict[uuid.UUID, list[uuid.UUID]] = {}
        for v in vinculos:
            por_alerta.setdefault(v.alerta_id, []).append(v.incidente_id)
        return {alerta_id: tuple(ids) for alerta_id, ids in por_alerta.items()}

    async def replace_for_liquidacion(
        self, liquidacion_id: UUID, alertas: Sequence[AlertaConciliada]
    ) -> list[Alerta]:
        await self._session.execute(
            delete(AlertaModel).where(AlertaModel.liquidacion_id == liquidacion_id)
        )
        modelos = [_a_model(liquidacion_id, a) for a in alertas]
        self._session.add_all(modelos)
        await self._session.flush()
        self._session.add_all(_a_vinculos(modelos, alertas))
        await self._session.flush()
        for modelo in modelos:
            await self._session.refresh(modelo)
        grupos = {
            m.id: a.generada.grupo_incidente_ids
            for m, a in zip(modelos, alertas, strict=True)
        }
        return [_to_entity(m, grupos[m.id]) for m in modelos]

    async def update_estado(
        self,
        liquidacion_id: UUID,
        alerta_id: UUID,
        *,
        estado: str,
        justificacion: str | None,
        incidente_relacionado_id: UUID | None = None,
    ) -> Alerta | None:
        row = await self._session.get(AlertaModel, alerta_id)
        if row is None or row.liquidacion_id != liquidacion_id:
            return None
        row.estado = estado
        row.justificacion = justificacion
        row.incidente_relacionado_id = incidente_relacionado_id
        await self._session.flush()
        await self._session.refresh(row)
        grupos = await self._grupo_incidente_ids([row.id] if row.es_grupo else [])
        return _to_entity(row, grupos.get(row.id, ()))


def _a_model(liquidacion_id: UUID, conciliada: AlertaConciliada) -> AlertaModel:
    alerta = conciliada.generada
    return AlertaModel(
        id=uuid.uuid4(),
        incidente_id=alerta.incidente_id,
        liquidacion_id=liquidacion_id,
        tipo_alerta=alerta.tipo_alerta,
        descripcion=alerta.descripcion,
        datos_contexto=alerta.datos_contexto,
        riesgo=alerta.riesgo,
        estado=conciliada.estado,
        justificacion=conciliada.justificacion,
        incidente_relacionado_id=conciliada.incidente_relacionado_id,
        es_grupo=alerta.es_grupo,
        monto_cobrado=alerta.monto_cobrado,
        monto_esperado=alerta.monto_esperado,
        diferencia=alerta.diferencia,
    )


def _a_vinculos(
    modelos: list[AlertaModel], alertas: Sequence[AlertaConciliada]
) -> list[AlertaIncidenteModel]:
    vinculos = []
    for modelo, conciliada in zip(modelos, alertas, strict=True):
        alerta = conciliada.generada
        if not alerta.es_grupo:
            continue
        vinculos += [
            AlertaIncidenteModel(
                id=uuid.uuid4(),
                alerta_id=modelo.id,
                incidente_id=incidente_id,
                rol=ROL_PRINCIPAL if incidente_id == alerta.incidente_id else ROL_REFERENCIA,
            )
            for incidente_id in alerta.grupo_incidente_ids
        ]
    return vinculos


def _to_entity(row: AlertaModel, grupo_incidente_ids: tuple[uuid.UUID, ...]) -> Alerta:
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
        justificacion=row.justificacion,
        incidente_relacionado_id=row.incidente_relacionado_id,
        es_grupo=row.es_grupo,
        grupo_incidente_ids=grupo_incidente_ids,
        monto_cobrado=row.monto_cobrado,
        monto_esperado=row.monto_esperado,
        diferencia=row.diferencia,
    )
