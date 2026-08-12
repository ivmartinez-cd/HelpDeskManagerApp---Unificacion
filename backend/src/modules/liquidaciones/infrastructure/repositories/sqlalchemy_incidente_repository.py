"""Implementación Postgres del puerto IncidenteRepository (tabla incidentes)."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import (
    IncidenteEvaluado,
)
from src.modules.liquidaciones.infrastructure.models.incidente_model import IncidenteModel
from src.modules.liquidaciones.infrastructure.models.liquidacion_model import LiquidacionModel


class SqlAlchemyIncidenteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[Incidente]:
        stmt = select(IncidenteModel).where(IncidenteModel.liquidacion_id == liquidacion_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def list_by_prestador(self, prestador_id: UUID) -> list[Incidente]:
        stmt = (
            select(IncidenteModel)
            .join(LiquidacionModel, LiquidacionModel.id == IncidenteModel.liquidacion_id)
            .where(LiquidacionModel.prestador_id == prestador_id)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def apply_evaluacion(self, resultados: Sequence[IncidenteEvaluado]) -> None:
        for r in resultados:
            stmt = (
                update(IncidenteModel)
                .where(IncidenteModel.id == r.incidente_id)
                .values(
                    costo_servicio_esperado=r.costo_servicio_esperado,
                    cant_km_esperado=r.cant_km_esperado,
                    costo_km_esperado=r.costo_km_esperado,
                    estado_validacion=r.estado_validacion,
                )
            )
            await self._session.execute(stmt)


def _to_entity(row: IncidenteModel) -> Incidente:
    return Incidente(
        id=row.id,
        liquidacion_id=row.liquidacion_id,
        numero_incidente=row.numero_incidente,
        rubro=row.rubro,
        tipo=row.tipo,
        empresa_nombre=row.empresa_nombre,
        sucursal_nombre=row.sucursal_nombre,
        nro_serie=row.nro_serie,
        fecha_cierre=row.fecha_cierre,
        costo_servicio_cobrado=row.costo_servicio_cobrado,
        cant_km_cobrado=row.cant_km_cobrado,
        costo_km_cobrado=row.costo_km_cobrado,
        total_viaje_cobrado=row.total_viaje_cobrado,
        costo_total_cobrado=row.costo_total_cobrado,
        pasa_it=row.pasa_it,
        costo_servicio_esperado=row.costo_servicio_esperado,
        cant_km_esperado=row.cant_km_esperado,
        costo_km_esperado=row.costo_km_esperado,
        estado_validacion=row.estado_validacion,
    )
