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
from src.modules.insumos.presentation.devices_router import router as insumos_devices_router
from src.modules.insumos.presentation.requests_router import router as insumos_requests_router
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.logging_config import configure_logging
from src.shared.presentation.errors.handlers import register_exception_handlers
from src.shared.presentation.health.router import router as health_router
from src.shared.presentation.middlewares.request_id import RequestIdMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(level="DEBUG" if settings.environment == "development" else "INFO")

    app = FastAPI(title="HelpDesk Manager API", version="0.1.0")

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
    app.include_router(insumos_requests_router)
    app.include_router(insumos_devices_router)
    return app



app = create_app()
