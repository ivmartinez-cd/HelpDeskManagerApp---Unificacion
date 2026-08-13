"""Implementación Postgres del puerto ObservacionRepository (tablas observaciones /
observacion_incidentes)."""

import uuid
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.observacion import (
    ROL_PRINCIPAL,
    ROL_REFERENCIA,
    Observacion,
)
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import (
    ObservacionGenerada,
)
from src.modules.liquidaciones.infrastructure.models.observacion_model import (
    ObservacionIncidenteModel,
    ObservacionModel,
)


class SqlAlchemyObservacionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[Observacion]:
        stmt = select(ObservacionModel).where(ObservacionModel.liquidacion_id == liquidacion_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def update_estado(
        self, liquidacion_id: UUID, observacion_id: UUID, estado: str
    ) -> Observacion | None:
        row = await self._session.get(ObservacionModel, observacion_id)
        if row is None or row.liquidacion_id != liquidacion_id:
            return None
        row.estado = estado
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def replace_for_liquidacion(
        self, liquidacion_id: UUID, observaciones: Sequence[ObservacionGenerada]
    ) -> list[Observacion]:
        await self._session.execute(
            delete(ObservacionModel).where(ObservacionModel.liquidacion_id == liquidacion_id)
        )
        creadas = []
        for obs in observaciones:
            modelo = await self._crear_observacion(liquidacion_id, obs)
            creadas.append(_to_entity(modelo))
        return creadas

    async def _crear_observacion(
        self, liquidacion_id: UUID, obs: ObservacionGenerada
    ) -> ObservacionModel:
        modelo = _a_model(liquidacion_id, obs)
        self._session.add(modelo)
        await self._session.flush()
        self._session.add_all(_a_vinculos(modelo.id, obs))
        await self._session.flush()
        await self._session.refresh(modelo)
        return modelo


def _a_model(liquidacion_id: UUID, obs: ObservacionGenerada) -> ObservacionModel:
    return ObservacionModel(
        id=uuid.uuid4(),
        liquidacion_id=liquidacion_id,
        tipo_observacion=obs.tipo_observacion,
        severidad=obs.severidad,
        titulo=obs.titulo,
        descripcion=obs.descripcion,
        datos_contexto=obs.datos_contexto,
        monto_cobrado=obs.monto_cobrado,
        monto_esperado=obs.monto_esperado,
        diferencia=round(obs.monto_cobrado - obs.monto_esperado, 2),
        regla_codigo=obs.regla_codigo,
    )


def _a_vinculos(observacion_id: UUID, obs: ObservacionGenerada) -> list[ObservacionIncidenteModel]:
    return [
        ObservacionIncidenteModel(
            id=uuid.uuid4(),
            observacion_id=observacion_id,
            incidente_id=incidente_id,
            rol=ROL_PRINCIPAL if incidente_id == obs.incidente_principal_id else ROL_REFERENCIA,
        )
        for incidente_id in obs.incidentes_relacionados
    ]


def _to_entity(row: ObservacionModel) -> Observacion:
    return Observacion(
        id=row.id,
        liquidacion_id=row.liquidacion_id,
        tipo_observacion=row.tipo_observacion,
        severidad=row.severidad,
        titulo=row.titulo,
        descripcion=row.descripcion,
        datos_contexto=row.datos_contexto,
        monto_cobrado=row.monto_cobrado,
        monto_esperado=row.monto_esperado,
        diferencia=row.diferencia,
        estado=row.estado,
        regla_codigo=row.regla_codigo,
        fecha_generacion=row.fecha_generacion,
    )
