"""Job de fondo del módulo contadores:

Auto-sync (configurable vía settings):
- calendario_refresh: cada 15 min (configurable) — full replace de la ventana ±90 días
  leyendo la base de Gestión en ORION (ADR-047; antes, scraping de la web).
  Cada ciclo rehace el rango entero. El botón "Sincronizar" fuerza un ciclo
  inmediato aparte.

Sin ORION configurado, el ciclo falla con ExternalServiceError — se loguea y
se reintenta en el próximo intervalo."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from src.modules.contadores.application.use_cases.sync_calendar_events import (
    SyncCalendarEventsUseCase,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_calendario_repository import (
    SqlAlchemyCalendarEventRepository,
)
from src.modules.contadores.presentation.calendario_routers._deps import (
    DEFAULT_SYNC_WINDOW_DAYS,
)
from src.modules.contadores.presentation.dependencies import (
    get_gestion_calendario_gateway,
    get_operador_catalog_gateway,
)
from src.shared.infrastructure.database.session import get_sessionmaker

logger = logging.getLogger(__name__)


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


async def _ciclo_calendario() -> None:
    today = datetime.now(UTC).date()
    window = timedelta(days=DEFAULT_SYNC_WINDOW_DAYS)
    start_date = (today - window).isoformat()
    end_date = (today + window).isoformat()

    factory = get_sessionmaker()
    async with factory() as session:
        repo = SqlAlchemyCalendarEventRepository(session)
        use_case = SyncCalendarEventsUseCase(
            get_gestion_calendario_gateway(), get_operador_catalog_gateway(), repo
        )
        result = await use_case.execute(start_date=start_date, end_date=end_date)
        await session.commit()
    logger.info(
        "calendario_refresh: OK — eventos=%d operadores=%d rango=[%s, %s]",
        result.events_count,
        result.operadores_count,
        start_date,
        end_date,
    )


async def background_calendario_refresh_task(interval_minutes: int) -> None:
    await _loop("calendario_refresh", _ciclo_calendario, interval_minutes)


def start_contadores_background_jobs(interval_minutes: int) -> list[asyncio.Task[None]]:
    return [asyncio.create_task(background_calendario_refresh_task(interval_minutes))]
