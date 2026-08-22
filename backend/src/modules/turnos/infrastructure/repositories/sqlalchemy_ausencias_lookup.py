import uuid
from datetime import date
from typing import Any

from sqlalchemy import Row, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.turnos.domain.repositories.ausencias_lookup import (
    TIPO_VACACIONES,
    AusenciaAprobada,
)
from src.modules.vacaciones.infrastructure.models.ausencia_model import (
    VacacionesAusenciaModel,
)
from src.modules.vacaciones.infrastructure.models.empleado_model import VacacionesEmpleadoModel
from src.modules.vacaciones.infrastructure.models.solicitud_model import (
    VacacionesSolicitudModel,
)

_APROBADA = "APPROVED"


class SqlAlchemyAusenciasLookup:
    """Adaptador cruzado hacia vacaciones -- legal porque el contrato
    `turnos-domain-app-independent-from-vacaciones` solo prohíbe la dependencia
    desde domain/application (mismo patrón que `SqlAlchemyPrestadorLookup` en
    sla). Lee solicitudes de vacaciones APROBADAS y bajas APROBADAS
    (enfermedad, home office, cambio de horario…) de empleados con cuenta
    vinculada (`vacaciones_empleado.user_id`, D3 del README de vacaciones)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ausencias_aprobadas_en(
        self, user_ids: list[uuid.UUID], desde: date, hasta: date
    ) -> list[AusenciaAprobada]:
        if not user_ids:
            return []
        vacaciones = await self._vacaciones(user_ids, desde, hasta)
        bajas = await self._bajas(user_ids, desde, hasta)
        return sorted(vacaciones + bajas, key=lambda a: (a.desde, a.tipo))

    async def _vacaciones(
        self, user_ids: list[uuid.UUID], desde: date, hasta: date
    ) -> list[AusenciaAprobada]:
        stmt = (
            select(
                VacacionesEmpleadoModel.user_id,
                VacacionesSolicitudModel.start_date,
                VacacionesSolicitudModel.end_date,
            )
            .join(
                VacacionesSolicitudModel,
                VacacionesSolicitudModel.empleado_id == VacacionesEmpleadoModel.id,
            )
            .where(
                VacacionesEmpleadoModel.user_id.in_(user_ids),
                VacacionesSolicitudModel.status == _APROBADA,
                VacacionesSolicitudModel.start_date <= hasta,
                VacacionesSolicitudModel.end_date >= desde,
            )
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            AusenciaAprobada(user_id=user_id, desde=start, hasta=end, tipo=TIPO_VACACIONES)
            for user_id, start, end in rows
            if user_id is not None
        ]

    async def _bajas(
        self, user_ids: list[uuid.UUID], desde: date, hasta: date
    ) -> list[AusenciaAprobada]:
        stmt = _bajas_aprobadas_stmt(user_ids, desde, hasta)
        rows = (await self._session.execute(stmt)).all()
        return [_baja_desde_fila(row) for row in rows if row.user_id is not None]


# Orden de columnas = orden de desempaquetado en `_baja_desde_fila`.
_BAJA_COLUMNAS = (
    VacacionesEmpleadoModel.user_id,
    VacacionesAusenciaModel.start_date,
    VacacionesAusenciaModel.end_date,
    VacacionesAusenciaModel.tipo,
    VacacionesAusenciaModel.hora_desde,
    VacacionesAusenciaModel.hora_hasta,
)


def _bajas_aprobadas_stmt(user_ids: list[uuid.UUID], desde: date, hasta: date) -> Select[Any]:
    """Bajas APROBADAS de empleados vinculados que se solapan con [desde, hasta]."""
    return (
        select(*_BAJA_COLUMNAS)
        .join(
            VacacionesAusenciaModel,
            VacacionesAusenciaModel.empleado_id == VacacionesEmpleadoModel.id,
        )
        .where(
            VacacionesEmpleadoModel.user_id.in_(user_ids),
            VacacionesAusenciaModel.status == _APROBADA,
            VacacionesAusenciaModel.start_date <= hasta,
            VacacionesAusenciaModel.end_date >= desde,
        )
    )


def _baja_desde_fila(row: Row[Any]) -> AusenciaAprobada:
    user_id, start, end, tipo, hora_desde, hora_hasta = row
    return AusenciaAprobada(
        user_id=user_id,
        desde=start,
        hasta=end,
        tipo=tipo,
        hora_desde=hora_desde,
        hora_hasta=hora_hasta,
    )
