"""Job de fondo del módulo contadores:

Auto-sync (configurable vía settings):
- calendario_refresh: cada 120 min (2 h) — full replace de la ventana ±90 días
  contra Gestión Web. Gestión no expone un endpoint diff, así que cada ciclo
  rehace el rango entero. El botón "Sincronizar" fuerza un ciclo inmediato aparte.

Sin credenciales de Gestión configuradas, el ciclo falla con ExternalServiceError
— se loguea y se reintenta en el próximo intervalo."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from src.modules.contadores.application.use_cases.sync_calendar_events import (
    SyncCalendarEventsUseCase,
)
from src.modules.contadores.infrastructure.gestion.gestion_planificacion_client import (
    GestionPlanificacionClient,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_calendario_repository import (
    SqlAlchemyCalendarEventRepository,
)
from src.modules.contadores.presentation.calendario_routers._deps import (
    DEFAULT_SYNC_WINDOW_DAYS,
    SYNC_TIMEOUT_SECONDS,
)
from src.modules.contadores.presentation.dependencies import get_operador_catalog_gateway
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
        gestion = GestionPlanificacionClient(timeout=SYNC_TIMEOUT_SECONDS)
        operador_catalog = get_operador_catalog_gateway()
        use_case = SyncCalendarEventsUseCase(gestion, operador_catalog, repo)
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
