"""Copia los datos reales de `ftp_clients` y `meter_client_configs` desde el
Neon de producción de HelpDeskManager-Web al Postgres consolidado nuevo.
Script operativo de un solo uso (Fase 3 de Contadores, INTEGRACION_APPS_PLAN.md)
-- no forma parte del flujo de negocio de la app, por eso vive en scripts/ y no
en infrastructure/. Solo lee de Neon (nunca escribe ahí) e inserta usando los
repositorios reales del módulo nuevo, para no duplicar el mapeo fila->entidad.

Uso: `uv run python scripts/migrate_contadores_data_from_neon.py`
"""

import asyncio
import uuid

import asyncpg

from src.modules.contadores.domain.entities.ftp_client import FtpClient
from src.modules.contadores.domain.value_objects.meter_source import MeterSource
from src.modules.contadores.infrastructure.repositories.sqlalchemy_ftp_client_repository import (
    SqlAlchemyFtpClientRepository,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_meter_client_config_repository import (  # noqa: E501
    SqlAlchemyMeterClientConfigRepository,
)
from src.shared.infrastructure.database.session import get_sessionmaker

_NEON_DSN = (
    "postgresql://neondb_owner:npg_TF7LyjxW6kEO"
    "@ep-icy-smoke-adpxoqpt.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"
)


async def _migrate() -> None:
    source = await asyncpg.connect(_NEON_DSN)
    try:
        ftp_rows = await source.fetch(
            "SELECT name, host, \"user\", password, path, pattern FROM ftp_clients"
        )
        config_rows = await source.fetch(
            "SELECT source, customer_id, customer_name, suma_color FROM meter_client_configs"
        )
    finally:
        await source.close()

    session_factory = get_sessionmaker()
    async with session_factory() as session:
        ftp_repo = SqlAlchemyFtpClientRepository(session)
        for row in ftp_rows:
            existing = await ftp_repo.get_by_name(row["name"])
            if existing is not None:
                continue
            await ftp_repo.add(
                FtpClient(
                    id=uuid.uuid4(),
                    name=row["name"],
                    host=row["host"] or "",
                    user=row["user"] or "",
                    password=row["password"] or "",
                    path=row["path"] or "/",
                    pattern=row["pattern"] or "PrinterMonitorClient.db3.*",
                )
            )

        config_repo = SqlAlchemyMeterClientConfigRepository(session)
        for row in config_rows:
            await config_repo.upsert(
                source=MeterSource(row["source"]),
                customer_id=row["customer_id"],
                customer_name=row["customer_name"] or "",
                suma_color=bool(row["suma_color"]),
            )

        await session.commit()

    print(f"ftp_clients: {len(ftp_rows)} filas en origen")
    print(f"meter_client_configs: {len(config_rows)} filas en origen")


def main() -> None:
    asyncio.run(_migrate())


if __name__ == "__main__":
    main()
