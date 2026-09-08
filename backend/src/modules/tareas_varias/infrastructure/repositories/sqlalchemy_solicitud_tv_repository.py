import uuid

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.tareas_varias.domain.entities.solicitud_tv import EstadoSolicitudTv, SolicitudTv
from src.modules.tareas_varias.domain.value_objects.conteo_tv import ConteoTv
from src.modules.tareas_varias.domain.value_objects.periodo import Periodo
from src.modules.tareas_varias.infrastructure.models.solicitud_tv_model import SolicitudTvModel


def _row_to_entity(row: SolicitudTvModel) -> SolicitudTv:
    return SolicitudTv(
        id=row.id,
        id_tecnico=row.id_tecnico,
        tecnico=row.tecnico,
        fecha=row.fecha,
        razon_social=row.razon_social,
        sucursal=row.sucursal,
        tarea_realizada=row.tarea_realizada,
        estado=EstadoSolicitudTv(row.estado),
        creado_en=row.creado_en,
        resuelta_en=row.resuelta_en,
        resuelta_por_email=row.resuelta_por_email,
        motivo_rechazo=row.motivo_rechazo,
    )


class SqlAlchemySolicitudTvRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, solicitud: SolicitudTv) -> None:
        self._session.add(
            SolicitudTvModel(
                id=solicitud.id,
                id_tecnico=solicitud.id_tecnico,
                tecnico=solicitud.tecnico,
                periodo=solicitud.periodo,
                fecha=solicitud.fecha,
                razon_social=solicitud.razon_social,
                sucursal=solicitud.sucursal,
                tarea_realizada=solicitud.tarea_realizada,
                estado=solicitud.estado.value,
                creado_en=solicitud.creado_en,
                resuelta_en=solicitud.resuelta_en,
                resuelta_por_email=solicitud.resuelta_por_email,
                motivo_rechazo=solicitud.motivo_rechazo,
            )
        )
        await self._session.flush()

    async def get_by_id(self, solicitud_id: uuid.UUID) -> SolicitudTv | None:
        row = await self._session.get(SolicitudTvModel, solicitud_id)
        return _row_to_entity(row) if row is not None else None

    async def save(self, solicitud: SolicitudTv) -> None:
        row = await self._session.get(SolicitudTvModel, solicitud.id)
        assert row is not None, "save() requiere una solicitud ya persistida (usar add())"
        row.estado = solicitud.estado.value
        row.resuelta_en = solicitud.resuelta_en
        row.resuelta_por_email = solicitud.resuelta_por_email
        row.motivo_rechazo = solicitud.motivo_rechazo

    async def list_by_periodo(
        self,
        periodo: Periodo,
        *,
        estado: EstadoSolicitudTv | None = None,
        id_tecnico: int | None = None,
    ) -> list[SolicitudTv]:
        stmt = select(SolicitudTvModel).where(SolicitudTvModel.periodo == periodo.value)
        if estado is not None:
            stmt = stmt.where(SolicitudTvModel.estado == estado.value)
        if id_tecnico is not None:
            stmt = stmt.where(SolicitudTvModel.id_tecnico == id_tecnico)
        stmt = stmt.order_by(SolicitudTvModel.creado_en.desc())
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_row_to_entity(row) for row in rows]

    async def count_aprobadas_por_tecnico(self, periodo: Periodo) -> dict[int, int]:
        stmt = (
            select(SolicitudTvModel.id_tecnico, func.count())
            .where(
                SolicitudTvModel.periodo == periodo.value,
                SolicitudTvModel.estado == EstadoSolicitudTv.APROBADA.value,
            )
            .group_by(SolicitudTvModel.id_tecnico)
        )
        rows = (await self._session.execute(stmt)).all()
        return {id_tecnico: cantidad for id_tecnico, cantidad in rows}

    async def contar_por_tecnico_y_periodo(self, anio: int) -> dict[tuple[int, int], ConteoTv]:
        aprobadas_expr = func.sum(
            case((SolicitudTvModel.estado == EstadoSolicitudTv.APROBADA.value, 1), else_=0)
        )
        stmt = (
            select(
                SolicitudTvModel.id_tecnico,
                SolicitudTvModel.periodo,
                func.count(),
                aprobadas_expr,
            )
            .where(SolicitudTvModel.periodo.between(anio * 100 + 1, anio * 100 + 12))
            .group_by(SolicitudTvModel.id_tecnico, SolicitudTvModel.periodo)
        )
        rows = (await self._session.execute(stmt)).all()
        return {
            (id_tecnico, periodo): ConteoTv(solicitadas=solicitadas, aprobadas=int(aprobadas))
            for id_tecnico, periodo, solicitadas, aprobadas in rows
        }
