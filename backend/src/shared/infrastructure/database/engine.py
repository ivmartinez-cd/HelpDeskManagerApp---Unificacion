from functools import lru_cache

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.shared.infrastructure.config.settings import get_settings


def _as_async_url(raw_url: str) -> str:
    """DATABASE_URL usa el esquema genérico `postgresql://`; el driver async
    (`asyncpg`) se agrega acá para no acoplar el .env a una librería concreta."""
    url = make_url(raw_url)
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+asyncpg")
    return url.render_as_string(hide_password=False)


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()
    async_url = _as_async_url(settings.database_url.get_secret_value())
    return create_async_engine(async_url, pool_pre_ping=True)
