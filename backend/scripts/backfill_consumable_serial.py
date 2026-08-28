"""Completa consumable_serial en TODO el historial de processed_requests que se quedó
sin ese dato — el chequeo periódico del poller (ver background_jobs.py) solo cubre los
últimos 7 días. Uso: `uv run python scripts/backfill_consumable_serial.py [--dry-run]`.

Script operativo, fuera de las capas domain/application/infrastructure: corre contra la
DB real de la instancia donde se ejecuta (DATABASE_URL del .env local) — confirmar el
entorno antes de correrlo sin --dry-run (ver CLAUDE.md, "Modo test obligatorio").
"""

import argparse
import asyncio

from src.modules.insumos.application.use_cases.backfill_consumable_serial import (
    BackfillConsumableSerial,
    BackfillConsumableSerialPorts,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_processed_request_repository import (  # noqa: E501
    SqlAlchemyProcessedRequestRepository,
)
from src.modules.insumos.presentation.wiring import get_insight_gateway
from src.shared.infrastructure.database.session import get_sessionmaker


async def _run(dry_run: bool) -> None:
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        processed = SqlAlchemyProcessedRequestRepository(session)
        missing = await processed.get_missing_consumable_serial(within_days=None)
        print(f"Pedidos sin consumable_serial: {len(missing)}")
        if not missing:
            return
        if dry_run:
            print("--dry-run: no se escribe nada. Ejemplo de candidatos (hasta 20):")
            for row in missing[:20]:
                print(f"  hp_request_id={row.hp_request_id} customer_id={row.customer_id}")
            return
        ports = BackfillConsumableSerialPorts(insight=get_insight_gateway(), processed=processed)
        fixed = await BackfillConsumableSerial(ports).execute(within_days=None)
        await session.commit()
        print(f"Completados: {fixed}/{len(missing)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Solo listar candidatos")
    args = parser.parse_args()
    asyncio.run(_run(args.dry_run))


if __name__ == "__main__":
    main()
