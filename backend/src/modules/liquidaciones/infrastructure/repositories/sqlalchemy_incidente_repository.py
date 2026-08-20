"""Implementación Postgres del puerto IncidenteRepository (tabla incidentes)."""

import uuid
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.value_objects.incidente_actualizado import (
    IncidenteActualizado,
)
from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    IncidenteImportado,
)
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

    async def bulk_create(
        self, liquidacion_id: UUID, incidentes: Sequence[IncidenteImportado]
    ) -> list[Incidente]:
        if not incidentes:
            return []
        modelos = [_a_model(liquidacion_id, i) for i in incidentes]
        self._session.add_all(modelos)
        await self._session.flush()
        for modelo in modelos:
            await self._session.refresh(modelo)
        return [_to_entity(m) for m in modelos]

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

    async def empresas_con_actividad_reciente(
        self, prestador_id: UUID, desde_periodo: str
    ) -> set[str]:
        stmt = (
            select(IncidenteModel.empresa_nombre)
            .distinct()
            .join(LiquidacionModel, LiquidacionModel.id == IncidenteModel.liquidacion_id)
            .where(
                LiquidacionModel.prestador_id == prestador_id,
                LiquidacionModel.periodo >= desde_periodo,
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return {r for r in rows if r is not None}

    async def update_cobrados(self, cambios: Sequence[IncidenteActualizado]) -> None:
        for c in cambios:
            stmt = (
                update(IncidenteModel)
                .where(IncidenteModel.id == c.incidente_id)
                .values(
                    rubro=c.rubro,
                    tipo=c.tipo,
                    empresa_nombre=c.empresa_nombre,
                    sucursal_nombre=c.sucursal_nombre,
                    nro_serie=c.nro_serie,
                    fecha_cierre=c.fecha_cierre,
                    costo_servicio_cobrado=c.costo_servicio_cobrado,
                    cant_km_cobrado=c.cant_km_cobrado,
                    costo_km_cobrado=c.costo_km_cobrado,
                    total_viaje_cobrado=c.total_viaje_cobrado,
                    costo_total_cobrado=c.costo_total_cobrado,
                    pasa_it=c.pasa_it,
                )
            )
            await self._session.execute(stmt)

    async def delete_by_ids(self, incidente_ids: Sequence[UUID]) -> int:
        from sqlalchemy.engine import CursorResult

        if not incidente_ids:
            return 0
        stmt = delete(IncidenteModel).where(IncidenteModel.id.in_(incidente_ids))
        result: CursorResult[tuple[()]] = await self._session.execute(  # type: ignore[assignment]
            stmt
        )
        return int(result.rowcount)

    async def update_estado_validacion(self, incidente_id: UUID, estado: str) -> None:
        stmt = (
            update(IncidenteModel)
            .where(IncidenteModel.id == incidente_id)
            .values(estado_validacion=estado)
        )
        await self._session.execute(stmt)


def _a_model(liquidacion_id: UUID, incidente: IncidenteImportado) -> IncidenteModel:
    return IncidenteModel(
        id=uuid.uuid4(),
        liquidacion_id=liquidacion_id,
        numero_incidente=incidente.numero_incidente,
        rubro=incidente.rubro,
        tipo=incidente.tipo,
        empresa_nombre=incidente.empresa_nombre,
        sucursal_nombre=incidente.sucursal_nombre,
        nro_serie=incidente.nro_serie,
        fecha_cierre=incidente.fecha_cierre,
        costo_servicio_cobrado=incidente.costo_servicio_cobrado,
        cant_km_cobrado=incidente.cant_km_cobrado,
        costo_km_cobrado=incidente.costo_km_cobrado,
        total_viaje_cobrado=incidente.total_viaje_cobrado,
        costo_total_cobrado=incidente.costo_total_cobrado,
        pasa_it=incidente.pasa_it,
    )


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
