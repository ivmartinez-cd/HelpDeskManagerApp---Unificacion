"""Corre BackfillEstadoLiquidaciones desde línea de comandos.

Uso:
  # dry-run (default, no escribe nada):
  docker exec helpdesk-manager-backend uv run python scripts/run_backfill_dryrun.py

  # real (escribe en la DB local — NO toca wsAyC):
  docker exec helpdesk-manager-backend uv run python scripts/run_backfill_dryrun.py --ejecutar

  # acotado a un prestador:
  docker exec helpdesk-manager-backend uv run python scripts/run_backfill_dryrun.py --ejecutar --prestador-id <uuid>
"""
import argparse
import asyncio
import os
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.modules.liquidaciones.application.use_cases.backfill_estado_liquidaciones import (
    BackfillEstadoLiquidaciones,
    BackfillEstadoLiquidacionesPorts,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_liquidacion_repository import (  # noqa: E501
    SqlAlchemyLiquidacionRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.soap.zeep_cd_liquidaciones_gateway import (
    ZeepCdLiquidacionesGateway,
)

DATABASE_URL = os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+asyncpg://", 1)


async def main(*, dry_run: bool, prestador_id: UUID | None) -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        use_case = BackfillEstadoLiquidaciones(
            BackfillEstadoLiquidacionesPorts(
                cd_gateway=ZeepCdLiquidacionesGateway(),
                prestadores=SqlAlchemyPrestadorRepository(session),
                liquidaciones=SqlAlchemyLiquidacionRepository(session),
            )
        )
        resultado = await use_case.execute(dry_run=dry_run, prestador_id=prestador_id)
        if not dry_run:
            await session.commit()

    label = "DRY-RUN" if dry_run else "EJECUTADO"
    print(f"\n{'='*60}")
    print(f"BACKFILL {label}  —  dry_run={resultado.dry_run}")
    print(f"{'='*60}")
    key = "que cambiarían" if dry_run else "actualizadas"
    print(f"  Total {key:<18}: {resultado.total_actualizadas}")
    print(f"  Saltadas (no abierta)  : {resultado.total_saltadas}")
    print(f"\n  Distribución por estado destino:")
    for estado, cnt in sorted(resultado.por_estado_destino.items(), key=lambda x: -x[1]):
        print(f"    {estado:<15} {cnt:>5}")

    print(f"\n  Detalle por prestador (solo con cambios):")
    for p in resultado.prestadores:
        if p.actualizadas or p.sin_match:
            print(
                f"    {p.prestador_nombre:<35}  "
                f"procesadas={p.procesadas}  "
                f"actualizadas={p.actualizadas}  "
                f"saltadas={p.saltadas}  "
                f"sin_match={p.sin_match}"
            )

    await engine.dispose()


parser = argparse.ArgumentParser()
parser.add_argument("--ejecutar", action="store_true", help="Escribe en DB (sin esto es dry-run)")
parser.add_argument("--prestador-id", type=UUID, default=None)
args = parser.parse_args()

asyncio.run(main(dry_run=not args.ejecutar, prestador_id=args.prestador_id))
