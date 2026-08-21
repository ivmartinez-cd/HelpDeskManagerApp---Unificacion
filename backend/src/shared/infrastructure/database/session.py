from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.shared.infrastructure.database.engine import get_engine


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=get_engine(), expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """El límite de transacción vive acá, no en cada repositorio: si el
    endpoint (y todo lo que haga con esta sesión) termina sin excepción, se
    comitea una sola vez; si algo lanza, `async with` hace rollback solo.

    Usar SIEMPRE como `Depends(get_db, scope="function")` (ADR-030): con el
    scope por defecto de FastAPI >= 0.118 ("request") este commit corre DESPUÉS
    de enviar la respuesta, así que el cliente podía recibir el 200 antes de que
    la escritura existiera (login → /me daba 401) y un error de commit pasaba
    después de haber respondido. `tests/unit/infrastructure/test_get_db_scope.py`
    falla si aparece una inyección de get_db sin scope."""
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        yield session
        await session.commit()
