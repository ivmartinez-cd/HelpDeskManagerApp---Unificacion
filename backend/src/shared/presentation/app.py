import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.repositories.operador_color_lookup import OperadorColorLookup
from src.modules.auth.presentation.dependencies.operador_colors import get_operador_color_lookup
from src.shared.infrastructure.config.settings import Settings, get_settings
from src.shared.infrastructure.cross_module.auth_operador_color_lookup import (
    SqlAlchemyOperadorColorLookup,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.infrastructure.logging_config import configure_logging
from src.shared.presentation.errors.handlers import register_exception_handlers
from src.shared.presentation.middlewares.request_id import RequestIdMiddleware
from src.shared.presentation.routers import ROUTERS

logger = logging.getLogger(__name__)


async def _provide_operador_color_lookup(
    db: AsyncSession = Depends(get_db, scope="function"),
) -> OperadorColorLookup:
    """Override real de `get_operador_color_lookup` (auth) — este archivo es
    el único punto del repo con permiso para conocer tanto a auth como a
    contadores; ver ADR-009."""
    return SqlAlchemyOperadorColorLookup(db)


def _jobs_insumos_y_sla(settings: Settings) -> list[asyncio.Task[None]]:
    """Van juntos porque comparten el mailer (el poller de insumos avisa por mail)."""
    from src.modules.auth.infrastructure.mailer_factory import get_mailer
    from src.modules.insumos.application.jobs.poller_alerts import PollerAlerts
    from src.modules.insumos.presentation.background_jobs import start_background_jobs
    from src.modules.insumos.presentation.mail_dispatch import LoggedMailDispatcher
    from src.modules.sla.presentation.background_jobs import start_sla_background_jobs

    mailer = get_mailer()
    poller_alerts = PollerAlerts(LoggedMailDispatcher(mailer))
    tasks = start_background_jobs(mailer, poller_alerts, settings.poll_interval_minutes)
    tasks += start_sla_background_jobs(settings.sla_refresh_interval_minutes)
    return tasks


def _jobs_analisis_log_hp(settings: Settings) -> list[asyncio.Task[None]]:
    from src.modules.analisis_log_hp.presentation.background_jobs import (
        start_analisis_log_hp_background_jobs,
    )

    return start_analisis_log_hp_background_jobs(settings.analisis_log_hp_snapshot_interval_minutes)


def _jobs_contadores(settings: Settings) -> list[asyncio.Task[None]]:
    from src.modules.contadores.presentation.background_jobs import (
        start_contadores_background_jobs,
    )

    return start_contadores_background_jobs(settings.calendario_refresh_interval_minutes)


def _jobs_liquidaciones(settings: Settings) -> list[asyncio.Task[None]]:
    from src.modules.liquidaciones.presentation.background_jobs import (
        start_liquidaciones_background_jobs,
    )

    return start_liquidaciones_background_jobs(settings.liquidaciones_reconciliar_interval_minutes)


def _jobs_wati(settings: Settings) -> list[asyncio.Task[None]]:
    from src.modules.wati.presentation.background_jobs import start_wati_background_jobs

    return start_wati_background_jobs(settings.wati_poll_interval_minutes)


def _iniciar_background_jobs(settings: Settings) -> list[asyncio.Task[None]]:
    """Imports perezosos a propósito: los módulos de jobs no se cargan (ni sus
    clientes externos) cuando `DISABLE_BACKGROUND_JOBS=true`. Mismo orden de
    arranque de siempre: insumos, sla, analisis_log_hp, contadores,
    liquidaciones, wati."""
    if settings.disable_background_jobs:
        return []
    tasks = _jobs_insumos_y_sla(settings)
    for arrancar in (_jobs_analisis_log_hp, _jobs_contadores, _jobs_liquidaciones, _jobs_wati):
        tasks += arrancar(settings)
    logger.info("background_jobs: %d job(s) iniciados", len(tasks))
    return tasks


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    tasks = _iniciar_background_jobs(get_settings())
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("background_jobs: %d job(s) cancelados", len(tasks))


def _origenes_cors(settings: Settings) -> list[str]:
    return list(
        filter(
            None,
            {
                settings.cors_origin,
                settings.frontend_url,
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3010",
                "http://127.0.0.1:3010",
            },
        )
    )


def _registrar_middlewares(app: FastAPI, settings: Settings) -> None:
    """CORS primero y RequestId después: el último agregado queda más afuera
    en la pila de Starlette (RequestId envuelve a CORS)."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origenes_cors(settings),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)


def _registrar_routers(app: FastAPI) -> None:
    for router in ROUTERS:
        app.include_router(router)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(level="DEBUG" if settings.environment == "development" else "INFO")

    app = FastAPI(title="HelpDesk Manager API", version="0.1.0", lifespan=_lifespan)
    app.dependency_overrides[get_operador_color_lookup] = _provide_operador_color_lookup
    _registrar_middlewares(app, settings)
    register_exception_handlers(app)
    _registrar_routers(app)
    return app


app = create_app()
