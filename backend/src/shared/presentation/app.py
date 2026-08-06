from fastapi import FastAPI

from src.modules.auth.presentation.admin_permissions_router import (
    router as admin_permissions_router,
)
from src.modules.auth.presentation.auth_router import router as auth_router
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.logging_config import configure_logging
from src.shared.presentation.errors.handlers import register_exception_handlers
from src.shared.presentation.health.router import router as health_router
from src.shared.presentation.middlewares.request_id import RequestIdMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(level="DEBUG" if settings.environment == "development" else "INFO")

    app = FastAPI(title="HelpDesk Manager API", version="0.1.0")
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(admin_permissions_router)
    return app


app = create_app()
