import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.turnos.domain.repositories.ausencias_lookup import AusenciaAprobada
from src.modules.vacaciones.infrastructure.models.empleado_model import VacacionesEmpleadoModel
from src.modules.vacaciones.infrastructure.models.solicitud_model import (
    VacacionesSolicitudModel,
)

_APROBADA = "APPROVED"


class SqlAlchemyAusenciasLookup:
    """Adaptador cruzado hacia vacaciones -- legal porque el contrato
    `turnos-domain-app-independent-from-vacaciones` solo prohíbe la dependencia
    desde domain/application (mismo patrón que `SqlAlchemyPrestadorLookup` en
    sla). Lee solicitudes APROBADAS de empleados con cuenta vinculada
    (`vacaciones_empleado.user_id`, D3 del README de vacaciones)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ausencias_aprobadas_en(
        self, user_ids: list[uuid.UUID], desde: date, hasta: date
    ) -> list[AusenciaAprobada]:
        if not user_ids:
            return []
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
            .order_by(VacacionesSolicitudModel.start_date)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            AusenciaAprobada(user_id=user_id, desde=start, hasta=end)
            for user_id, start, end in rows
            if user_id is not None
        ]
