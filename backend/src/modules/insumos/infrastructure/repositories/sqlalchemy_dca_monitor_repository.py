"""Implementación Postgres del puerto DcaMonitorRepository (tabla dca_monitors)."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.dca_monitor import DcaMonitorStatus, MonitorKey
from src.modules.insumos.infrastructure.models.dca_monitor_model import DcaMonitorModel

_ACTIVE_STATUS = "ACTIVE"


class SqlAlchemyDcaMonitorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, entries: Sequence[DcaMonitorStatus]) -> None:
        if not entries:
            return
        stmt = insert(DcaMonitorModel).values(
            [
                {
                    "customer_id": e.customer_id,
                    "monitor_name": e.monitor_name,
                    "online": e.online,
                    "status": e.status,
                    "last_contact": e.last_contact,
                    "checked_at": e.checked_at,
                }
                for e in entries
            ]
        )
        await self._session.execute(
            stmt.on_conflict_do_update(
                index_elements=["customer_id", "monitor_name"],
                set_={
                    "online": stmt.excluded.online,
                    "status": stmt.excluded.status,
                    "last_contact": stmt.excluded.last_contact,
                    "checked_at": stmt.excluded.checked_at,
                },
            )
        )

    async def list_offline_monitors(self, stale_hours: int) -> set[MonitorKey]:
        """online=False + status=ACTIVE + last_contact vencido (igual que el legacy).

        Usar last_contact del monitor (no checked_at) hace que la detección sea robusta
        a que el poller esté pausado: un monitor offline sigue siendo offline aunque no
        hayamos re-verificado hoy. Con checked_at >= cutoff, si el job no corre el dato
        envejece y todos los outages desaparecen de la lista — comportamiento incorrecto.
        """
        cutoff = datetime.now(UTC) - timedelta(hours=stale_hours)
        stmt = select(
            DcaMonitorModel.customer_id, DcaMonitorModel.monitor_name
        ).where(
            DcaMonitorModel.online.is_(False),
            DcaMonitorModel.status == _ACTIVE_STATUS,
            or_(
                DcaMonitorModel.last_contact.is_(None),
                DcaMonitorModel.last_contact < cutoff,
            ),
        )
        rows = (await self._session.execute(stmt)).all()
        return {MonitorKey(customer_id, monitor_name) for customer_id, monitor_name in rows}

    async def list_online_customer_ids(self) -> set[int]:
        stmt = (
            select(DcaMonitorModel.customer_id)
            .where(DcaMonitorModel.online.is_(True))
            .distinct()
        )
        return set((await self._session.execute(stmt)).scalars().all())
