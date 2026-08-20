import uuid
from datetime import date, timedelta

from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.turnos.infrastructure.models.turno_models import (
    TurnoAsignacionModel,
    TurnoSlotModel,
)

_DIAS_SEMANA = 7


class SqlAlchemyImpactoTurnosLookup:
    """Adaptador cruzado hacia turnos -- legal porque el contrato
    `vacaciones-domain-app-independent-from-turnos` solo prohíbe la dependencia
    desde domain/application (mismo patrón que `SqlAlchemyPrestadorLookup` en
    sla). Una asignación "afecta" al rango si está vigente en algún día del
    rango y el `dia_semana` de su franja cae dentro del rango (un rango de 7+
    días cubre todos los días de semana)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def tiene_turnos_en(self, user_id: uuid.UUID, desde: date, hasta: date) -> bool:
        if hasta < desde:
            return False
        stmt = select(
            exists().where(
                TurnoAsignacionModel.user_id == user_id,
                TurnoAsignacionModel.vigente_desde <= hasta,
                or_(
                    TurnoAsignacionModel.vigente_hasta.is_(None),
                    TurnoAsignacionModel.vigente_hasta >= desde,
                ),
                TurnoSlotModel.id == TurnoAsignacionModel.slot_id,
                TurnoSlotModel.dia_semana.in_(_dias_semana_en(desde, hasta)),
            )
        )
        return bool((await self._session.execute(stmt)).scalar())


def _dias_semana_en(desde: date, hasta: date) -> list[int]:
    cantidad = min((hasta - desde).days + 1, _DIAS_SEMANA)
    return sorted({(desde + timedelta(days=i)).weekday() for i in range(cantidad)})
