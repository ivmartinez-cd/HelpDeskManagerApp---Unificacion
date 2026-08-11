import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.modules.auth.presentation.admin_permissions_router import (
    router as admin_permissions_router,
)
from src.modules.auth.presentation.admin_users_router import router as admin_users_router
from src.modules.auth.presentation.auth_router import router as auth_router
from src.modules.contadores.presentation.calendario_router import (
    router as calendario_router,
)
from src.modules.contadores.presentation.ers_router import router as ers_router
from src.modules.contadores.presentation.ftp_clients_router import router as ftp_clients_router
from src.modules.contadores.presentation.sds_router import router as sds_router
from src.modules.contadores.presentation.tools_router import router as contadores_tools_router
from src.modules.insumos.presentation.alerts_router import router as insumos_alerts_router
from src.modules.insumos.presentation.config_router import router as insumos_config_router
from src.modules.insumos.presentation.customers_router import router as insumos_customers_router
from src.modules.insumos.presentation.devices_router import router as insumos_devices_router
from src.modules.insumos.presentation.mail_log_router import router as insumos_mail_log_router
from src.modules.insumos.presentation.new_devices_router import (
    router as insumos_new_devices_router,
)
from src.modules.insumos.presentation.offline_devices_router import (
    router as insumos_offline_devices_router,
)
from src.modules.insumos.presentation.requests_router import router as insumos_requests_router
from src.modules.insumos.presentation.statistics_router import (
    router as insumos_statistics_router,
)
from src.modules.sla.presentation.sla_router import router as sla_router
from src.modules.turnos.presentation.turnos_router import router as turnos_router
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.logging_config import configure_logging
from src.shared.presentation.errors.handlers import register_exception_handlers
from src.shared.presentation.health.router import router as health_router
from src.shared.presentation.middlewares.request_id import RequestIdMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    tasks: list[asyncio.Task[None]] = []
    if not settings.disable_background_jobs:
        from src.modules.auth.infrastructure.mailer_factory import get_mailer
        from src.modules.insumos.application.jobs.poller_alerts import PollerAlerts
        from src.modules.insumos.domain.value_objects.insumos_settings import (
            logistics_recipients,
            settings_from_raw,
        )
        from src.modules.insumos.infrastructure.repositories.sqlalchemy_insumos_settings_repository import (  # noqa: E501
            SqlAlchemyInsumosSettingsRepository,
        )
        from src.modules.insumos.presentation.background_jobs import start_background_jobs
        from src.shared.infrastructure.database.session import get_sessionmaker

        factory = get_sessionmaker()
        async with factory() as session:
            raw = await SqlAlchemyInsumosSettingsRepository(session).get_all()
        insumos_settings = settings_from_raw(raw)
        mailer = get_mailer()
        poller_alerts = PollerAlerts(
            mailer=mailer,
            recipients=logistics_recipients(insumos_settings),
        )
        tasks = start_background_jobs(mailer, poller_alerts, settings.poll_interval_minutes)
        logger.info("background_jobs: %d job(s) iniciados", len(tasks))
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("background_jobs: %d job(s) cancelados", len(tasks))


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(level="DEBUG" if settings.environment == "development" else "INFO")

    app = FastAPI(title="HelpDesk Manager API", version="0.1.0", lifespan=_lifespan)

    origins = list(filter(None, {
        settings.cors_origin,
        settings.frontend_url,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3010",
        "http://127.0.0.1:3010",
    }))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(admin_permissions_router)
    app.include_router(admin_users_router)
    app.include_router(contadores_tools_router)
    app.include_router(ftp_clients_router)
    app.include_router(sds_router)
    app.include_router(ers_router)
    app.include_router(calendario_router)
    app.include_router(insumos_customers_router)
    app.include_router(insumos_requests_router)
    app.include_router(insumos_devices_router)
    app.include_router(insumos_statistics_router)
    app.include_router(insumos_mail_log_router)
    app.include_router(insumos_config_router)
    app.include_router(insumos_new_devices_router)
    app.include_router(insumos_offline_devices_router)
    app.include_router(insumos_alerts_router)
    app.include_router(turnos_router)
    app.include_router(sla_router)
    return app


app = create_app()
