"""Job de fondo del módulo sla — refresca el snapshot del período actual cada
SLA_REFRESH_INTERVAL_MINUTES para que Inicio y /sla lean de un cache tibio en
vez de pegarle a MERCURIO en cada carga (~40s por consulta).

Si SLA_MERCURIO_HOST no está configurado, get_sla_query_gateway() lanza
ExternalServiceError en cada ciclo — se loguea y se reintenta en el próximo
intervalo, mismo criterio que el resto de los jobs opcionales por entorno."""

import asyncio
import logging
from datetime import UTC, datetime

from src.modules.sla.application.use_cases.refresh_sla_snapshot import RefreshSlaSnapshot
from src.modules.sla.infrastructure.repositories.sqlalchemy_sla_snapshot_repository import (
    SqlAlchemySlaSnapshotRepository,
)
from src.modules.sla.presentation.dependencies import get_sla_query_gateway
from src.shared.infrastructure.database.session import get_sessionmaker

logger = logging.getLogger(__name__)


def _periodo_actual() -> int:
    now = datetime.now(UTC)
    return now.year * 100 + now.month


async def background_sla_refresh_task(interval_minutes: int) -> None:
    logger.info("sla_refresh: iniciando (intervalo %d min)", interval_minutes)
    while True:
        try:
            factory = get_sessionmaker()
            async with factory() as session:
                repo = SqlAlchemySlaSnapshotRepository(session)
                use_case = RefreshSlaSnapshot(get_sla_query_gateway(), repo)
                snapshot = await use_case.execute(_periodo_actual())
                await session.commit()
            logger.info(
                "sla_refresh: OK — periodo=%d total=%d vencidos=%d",
                snapshot.periodo,
                snapshot.total,
                snapshot.vencidos,
            )
        except Exception as exc:
            logger.error("sla_refresh: ciclo fallido", exc_info=exc)
        await asyncio.sleep(interval_minutes * 60)


def start_sla_background_jobs(interval_minutes: int) -> list[asyncio.Task[None]]:
    return [asyncio.create_task(background_sla_refresh_task(interval_minutes))]
