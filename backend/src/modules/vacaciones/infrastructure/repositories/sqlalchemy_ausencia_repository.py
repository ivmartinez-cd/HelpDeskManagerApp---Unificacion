import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.solicitud import (
    ESTADOS_ACTIVOS,
    EstadoSolicitud,
)
from src.modules.vacaciones.domain.repositories.ausencia_repository import (
    FiltrosAusencias,
)
from src.modules.vacaciones.infrastructure.models.ausencia_model import (
    VacacionesAusenciaModel,
)
from src.modules.vacaciones.infrastructure.models.empleado_model import (
    VacacionesEmpleadoModel,
)

_ACTIVOS = [estado.value for estado in ESTADOS_ACTIVOS]


def _to_entity(row: VacacionesAusenciaModel) -> Ausencia:
    return Ausencia(
        id=row.id,
        empleado_id=row.empleado_id,
        start_date=row.start_date,
        end_date=row.end_date,
        days_count=row.days_count,
        half_day=row.half_day,
        tipo=TipoAusencia(row.tipo),
        reason=row.reason,
        status=EstadoSolicitud(row.status),
        created_at=row.created_at,
    )


class SqlAlchemyAusenciaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, ausencia_id: uuid.UUID) -> Ausencia | None:
        row = await self._session.get(VacacionesAusenciaModel, ausencia_id)
        return _to_entity(row) if row else None

    async def list_filtradas(self, filtros: FiltrosAusencias) -> list[Ausencia]:
        stmt = select(VacacionesAusenciaModel).order_by(
            VacacionesAusenciaModel.start_date.desc()
        )
        if filtros.status is not None:
            stmt = stmt.where(VacacionesAusenciaModel.status == filtros.status.value)
        if filtros.tipo is not None:
            stmt = stmt.where(VacacionesAusenciaModel.tipo == filtros.tipo.value)
        if filtros.empleado_id is not None:
            stmt = stmt.where(VacacionesAusenciaModel.empleado_id == filtros.empleado_id)
        if filtros.department_id is not None:
            stmt = stmt.join(
                VacacionesEmpleadoModel,
                VacacionesEmpleadoModel.id == VacacionesAusenciaModel.empleado_id,
            ).where(VacacionesEmpleadoModel.department_id == filtros.department_id)
        if filtros.desde is not None:
            stmt = stmt.where(VacacionesAusenciaModel.start_date >= filtros.desde)
        if filtros.hasta is not None:
            stmt = stmt.where(VacacionesAusenciaModel.start_date <= filtros.hasta)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def existe_activa_solapada(
        self,
        empleado_id: uuid.UUID,
        tipo: TipoAusencia,
        start: date,
        end: date,
        excluir_ausencia_id: uuid.UUID | None = None,
    ) -> bool:
        stmt = select(VacacionesAusenciaModel.id).where(
            VacacionesAusenciaModel.empleado_id == empleado_id,
            VacacionesAusenciaModel.tipo == tipo.value,
            VacacionesAusenciaModel.status.in_(_ACTIVOS),
            VacacionesAusenciaModel.start_date <= end,
            VacacionesAusenciaModel.end_date >= start,
        )
        if excluir_ausencia_id is not None:
            stmt = stmt.where(VacacionesAusenciaModel.id != excluir_ausencia_id)
        row = (await self._session.execute(stmt.limit(1))).scalar_one_or_none()
        return row is not None

    async def list_aprobadas_solapadas_de_empleados(
        self, empleado_ids: list[uuid.UUID], start: date, end: date
    ) -> list[Ausencia]:
        if not empleado_ids:
            return []
        stmt = select(VacacionesAusenciaModel).where(
            VacacionesAusenciaModel.empleado_id.in_(empleado_ids),
            VacacionesAusenciaModel.status == EstadoSolicitud.APPROVED.value,
            VacacionesAusenciaModel.start_date <= end,
            VacacionesAusenciaModel.end_date >= start,
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def add(self, ausencia: Ausencia) -> None:
        self._session.add(_to_model(ausencia))
        await self._session.flush()

    async def save(self, ausencia: Ausencia) -> None:
        row = await self._session.get(VacacionesAusenciaModel, ausencia.id)
        if row is None:
            return
        _apply(row, ausencia)
        await self._session.flush()

    async def delete(self, ausencia_id: uuid.UUID) -> None:
        row = await self._session.get(VacacionesAusenciaModel, ausencia_id)
        if row is not None:
            await self._session.delete(row)
            await self._session.flush()


def _to_model(ausencia: Ausencia) -> VacacionesAusenciaModel:
    row = VacacionesAusenciaModel(id=ausencia.id)
    _apply(row, ausencia)
    return row


def _apply(row: VacacionesAusenciaModel, ausencia: Ausencia) -> None:
    row.empleado_id = ausencia.empleado_id
    row.start_date = ausencia.start_date
    row.end_date = ausencia.end_date
    row.days_count = ausencia.days_count
    row.half_day = ausencia.half_day
    row.tipo = ausencia.tipo.value
    row.reason = ausencia.reason
    row.status = ausencia.status.value
