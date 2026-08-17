"""Jobs de fondo del módulo sla:
- SLA: refresca el snapshot del período actual (período mensual de vencidos).
- Pendientes: refresca el backlog de incidentes sin cerrar (transversal a
  períodos, se actualiza con cada cierre en Gestión).

Sin SLA_MERCURIO_HOST configurado, los gateways lanzan ExternalServiceError
en cada ciclo — se loguea y se reintenta en el próximo intervalo."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from src.modules.sla.application.use_cases.refresh_pendientes_snapshot import (
    RefreshPendientesSnapshot,
)
from src.modules.sla.application.use_cases.refresh_sla_snapshot import RefreshSlaSnapshot
from src.modules.sla.infrastructure.repositories.sqlalchemy_pendientes_snapshot_repository import (
    SqlAlchemyPendientesSnapshotRepository,
)
from src.modules.sla.infrastructure.repositories.sqlalchemy_prestador_lookup import (
    SqlAlchemyPrestadorLookup,
)
from src.modules.sla.infrastructure.repositories.sqlalchemy_sla_snapshot_repository import (
    SqlAlchemySlaSnapshotRepository,
)
from src.modules.sla.presentation.dependencies import (
    get_pendientes_query_gateway,
    get_sla_query_gateway,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_sessionmaker

logger = logging.getLogger(__name__)


def _periodo_actual() -> int:
    now = datetime.now(UTC)
    return now.year * 100 + now.month


async def _loop(
    nombre: str, ciclo: Callable[[], Awaitable[None]], interval_minutes: int
) -> None:
    """Corre `ciclo` cada `interval_minutes`; un ciclo fallido se loguea y se
    reintenta en el próximo intervalo, nunca corta el loop."""
    logger.info("%s: iniciando (intervalo %d min)", nombre, interval_minutes)
    while True:
        try:
            await ciclo()
        except Exception as exc:
            logger.error("%s: ciclo fallido", nombre, exc_info=exc)
        await asyncio.sleep(interval_minutes * 60)


async def _ciclo_sla() -> None:
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


async def _ciclo_pendientes() -> None:
    settings = get_settings()
    factory = get_sessionmaker()
    async with factory() as session:
        repo = SqlAlchemyPendientesSnapshotRepository(session)
        use_case = RefreshPendientesSnapshot(
            get_pendientes_query_gateway(),
            repo,
            pst_lookup=SqlAlchemyPrestadorLookup(session),
            meses_corte=settings.pendientes_meses_corte,
        )
        snapshot = await use_case.execute()
        await session.commit()
    logger.info(
        "pendientes_refresh: OK — total=%d por_prestador=%d",
        snapshot.total,
        len(snapshot.por_prestador),
    )


async def background_sla_refresh_task(interval_minutes: int) -> None:
    await _loop("sla_refresh", _ciclo_sla, interval_minutes)


async def background_pendientes_refresh_task(interval_minutes: int) -> None:
    await _loop("pendientes_refresh", _ciclo_pendientes, interval_minutes)


def start_sla_background_jobs(interval_minutes: int) -> list[asyncio.Task[None]]:
    settings = get_settings()
    return [
        asyncio.create_task(background_sla_refresh_task(interval_minutes)),
        asyncio.create_task(
            background_pendientes_refresh_task(settings.pendientes_refresh_interval_minutes)
        ),
    ]
