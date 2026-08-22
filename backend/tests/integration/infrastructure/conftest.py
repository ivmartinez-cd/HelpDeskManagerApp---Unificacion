import os
from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from src.shared.infrastructure.database import model_registry  # noqa: F401
from src.shared.infrastructure.database.base import Base

# Desde el host: localhost:5440 (puerto publicado por docker-compose.test.yml).
# Desde el contenedor del backend (`make test-integration`): DB_TEST_HOST=helpdesk-db-test
# y DB_TEST_PORT=5432, con el contenedor de test conectado a la red del backend.
_DB_TEST_HOST = os.environ.get("DB_TEST_HOST", "localhost")
_DB_TEST_PORT = os.environ.get("DB_TEST_PORT", "5440")
_TEST_DATABASE_URL = (
    "postgresql+asyncpg://helpdesk_test:helpdesk_test"
    f"@{_DB_TEST_HOST}:{_DB_TEST_PORT}/helpdesk_test"
)


@pytest_asyncio.fixture(scope="session")
async def _test_engine() -> AsyncIterator[AsyncEngine]:
    """Usa Base.metadata directo (no Alembic) para el schema de test: la
    reversibilidad de las migraciones ya se probó por separado (Etapa 3/4)."""
    engine = create_async_engine(_TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(_test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Transacción por test, siempre con rollback — tests independientes
    entre sí sin importar el orden de ejecución (§7.3 de la guía)."""
    async with _test_engine.connect() as conn:
        trans = await conn.begin()
        # join_transaction_mode="create_savepoint": el commit/flush que hace
        # cada repositorio abre un SAVEPOINT en vez de pisar la transacción
        # externa que este fixture va a rollbackear al final.
        session = AsyncSession(
            bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()
