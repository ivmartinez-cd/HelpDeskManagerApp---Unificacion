import uuid
from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.domain.entities.empleado import EstadoEmpleado
from src.modules.vacaciones.domain.entities.solicitud import (
    ESTADOS_ACTIVOS,
    EstadoSolicitud,
    Solicitud,
)
from src.modules.vacaciones.domain.repositories.solicitud_repository import (
    FiltrosSolicitudes,
    RangoSolapado,
)
from src.modules.vacaciones.infrastructure.models.empleado_model import VacacionesEmpleadoModel
from src.modules.vacaciones.infrastructure.models.solicitud_model import VacacionesSolicitudModel

_ACTIVOS = [estado.value for estado in ESTADOS_ACTIVOS]


def _to_entity(row: VacacionesSolicitudModel) -> Solicitud:
    return Solicitud(
        id=row.id,
        empleado_id=row.empleado_id,
        start_date=row.start_date,
        end_date=row.end_date,
        days_requested=row.days_requested,
        charged_to_year=row.charged_to_year,
        reason=row.reason,
        status=EstadoSolicitud(row.status),
        created_at=row.created_at,
    )


def _activas_solapadas(rango: RangoSolapado) -> Select[tuple[VacacionesSolicitudModel]]:
    stmt = select(VacacionesSolicitudModel).where(
        VacacionesSolicitudModel.status.in_(_ACTIVOS),
        VacacionesSolicitudModel.start_date <= rango.end,
        VacacionesSolicitudModel.end_date >= rango.start,
    )
    if rango.excluir_solicitud_id is not None:
        stmt = stmt.where(VacacionesSolicitudModel.id != rango.excluir_solicitud_id)
    return stmt


class SqlAlchemySolicitudRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, solicitud_id: uuid.UUID) -> Solicitud | None:
        row = await self._session.get(VacacionesSolicitudModel, solicitud_id)
        return _to_entity(row) if row else None

    async def list_filtradas(self, filtros: FiltrosSolicitudes) -> list[Solicitud]:
        stmt = select(VacacionesSolicitudModel).order_by(
            VacacionesSolicitudModel.start_date.desc()
        )
        if filtros.status is not None:
            stmt = stmt.where(VacacionesSolicitudModel.status == filtros.status.value)
        if filtros.empleado_id is not None:
            stmt = stmt.where(VacacionesSolicitudModel.empleado_id == filtros.empleado_id)
        if filtros.department_id is not None:
            stmt = stmt.join(
                VacacionesEmpleadoModel,
                VacacionesEmpleadoModel.id == VacacionesSolicitudModel.empleado_id,
            ).where(VacacionesEmpleadoModel.department_id == filtros.department_id)
        if filtros.desde is not None:
            stmt = stmt.where(VacacionesSolicitudModel.start_date >= filtros.desde)
        if filtros.hasta is not None:
            stmt = stmt.where(VacacionesSolicitudModel.start_date <= filtros.hasta)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_activas_de_empleado(
        self, empleado_id: uuid.UUID, excluir_solicitud_id: uuid.UUID | None = None
    ) -> list[Solicitud]:
        stmt = (
            select(VacacionesSolicitudModel)
            .where(
                VacacionesSolicitudModel.empleado_id == empleado_id,
                VacacionesSolicitudModel.status.in_(_ACTIVOS),
            )
            .order_by(VacacionesSolicitudModel.start_date)
        )
        if excluir_solicitud_id is not None:
            stmt = stmt.where(VacacionesSolicitudModel.id != excluir_solicitud_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_activas_de_empleados(
        self, empleado_ids: list[uuid.UUID]
    ) -> list[Solicitud]:
        if not empleado_ids:
            return []
        stmt = (
            select(VacacionesSolicitudModel)
            .where(
                VacacionesSolicitudModel.empleado_id.in_(empleado_ids),
                VacacionesSolicitudModel.status.in_(_ACTIVOS),
            )
            .order_by(VacacionesSolicitudModel.start_date)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_activas_solapadas_de_empleados(
        self, empleado_ids: list[uuid.UUID], rango: RangoSolapado
    ) -> list[Solicitud]:
        if not empleado_ids:
            return []
        stmt = _activas_solapadas(rango).where(
            VacacionesSolicitudModel.empleado_id.in_(empleado_ids)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_rangos_activos_por_cargo(
        self, cargo_id: uuid.UUID, excluir_empleado_id: uuid.UUID, rango: RangoSolapado
    ) -> list[tuple[date, date]]:
        stmt = (
            _activas_solapadas(rango)
            .join(
                VacacionesEmpleadoModel,
                VacacionesEmpleadoModel.id == VacacionesSolicitudModel.empleado_id,
            )
            .where(
                VacacionesEmpleadoModel.cargo_id == cargo_id,
                VacacionesEmpleadoModel.status == EstadoEmpleado.ACTIVE.value,
                VacacionesSolicitudModel.empleado_id != excluir_empleado_id,
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [(r.start_date, r.end_date) for r in rows]

    async def list_activas_solapadas_de_departamento(
        self, department_id: uuid.UUID, rango: RangoSolapado
    ) -> list[Solicitud]:
        stmt = (
            _activas_solapadas(rango)
            .join(
                VacacionesEmpleadoModel,
                VacacionesEmpleadoModel.id == VacacionesSolicitudModel.empleado_id,
            )
            .where(VacacionesEmpleadoModel.department_id == department_id)
            .order_by(VacacionesSolicitudModel.start_date)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_activas_en_rango(
        self, desde: date | None, hasta: date | None, department_id: uuid.UUID | None
    ) -> list[Solicitud]:
        stmt = select(VacacionesSolicitudModel).where(
            VacacionesSolicitudModel.status.in_(_ACTIVOS)
        )
        if desde is not None:
            stmt = stmt.where(VacacionesSolicitudModel.start_date >= desde)
        if hasta is not None:
            stmt = stmt.where(VacacionesSolicitudModel.start_date <= hasta)
        if department_id is not None:
            stmt = stmt.join(
                VacacionesEmpleadoModel,
                VacacionesEmpleadoModel.id == VacacionesSolicitudModel.empleado_id,
            ).where(VacacionesEmpleadoModel.department_id == department_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def add(self, solicitud: Solicitud) -> None:
        self._session.add(_to_model(solicitud))
        await self._session.flush()

    async def save(self, solicitud: Solicitud) -> None:
        row = await self._session.get(VacacionesSolicitudModel, solicitud.id)
        if row is None:
            return
        _apply(row, solicitud)
        await self._session.flush()

    async def delete(self, solicitud_id: uuid.UUID) -> None:
        row = await self._session.get(VacacionesSolicitudModel, solicitud_id)
        if row is not None:
            await self._session.delete(row)
            await self._session.flush()


def _to_model(solicitud: Solicitud) -> VacacionesSolicitudModel:
    row = VacacionesSolicitudModel(id=solicitud.id)
    _apply(row, solicitud)
    return row


def _apply(row: VacacionesSolicitudModel, solicitud: Solicitud) -> None:
    row.empleado_id = solicitud.empleado_id
    row.start_date = solicitud.start_date
    row.end_date = solicitud.end_date
    row.days_requested = solicitud.days_requested
    row.charged_to_year = solicitud.charged_to_year
    row.reason = solicitud.reason
    row.status = solicitud.status.value
