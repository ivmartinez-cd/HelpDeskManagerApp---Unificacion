"""Adapter del puerto ExclusiveLock usando advisory locks de Postgres.

Por qué conexión dedicada con AUTOCOMMIT y no la AsyncSession del request:
ver ADR-008. Las claves deben ser únicas en toda la base — mantener el registro
en este módulo (no dispersarlas en wiring o en los casos de uso).
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

# Registro central de claves — cada par de operaciones mutuamente excluyentes
# usa su propia clave para no bloquearse entre sí.
OFFLINE_VERIFY_LOCK_KEY: int = 1_001_001
OFFLINE_DELETE_LOCK_KEY: int = 1_001_002


class PostgresAdvisoryLock:
    """pg_try_advisory_lock sobre una conexión dedicada en AUTOCOMMIT.

    La conexión se abre y cierra con cada `hold()`: el lock está atado a la sesión
    de Postgres, no a una transacción, así que no interfiere con los commits del
    request normal. Ver ADR-008 para el detalle de la decisión.
    """

    def __init__(self, engine: AsyncEngine, lock_key: int) -> None:
        self._engine = engine
        self._lock_key = lock_key

    @asynccontextmanager
    async def hold(self) -> AsyncGenerator[bool, None]:
        async with self._engine.connect() as conn:
            await conn.execution_options(isolation_level="AUTOCOMMIT")
            row = await conn.execute(
                text("SELECT pg_try_advisory_lock(:key)"), {"key": self._lock_key}
            )
            acquired: bool = row.scalar_one()
            try:
                yield acquired
            finally:
                if acquired:
                    await conn.execute(
                        text("SELECT pg_advisory_unlock(:key)"), {"key": self._lock_key}
                    )
