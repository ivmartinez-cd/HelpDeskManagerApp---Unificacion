"""Job de fondo del módulo analisis-log-hp: snapshots SDS automáticos 2×/día.

Corre bajo DISABLE_BACKGROUND_JOBS igual que los demás módulos (CLAUDE.md).
No se activa solo — solo arranca si el orquestador central (app.py) lo llama.
"""

import asyncio
import logging

from src.modules.analisis_log_hp.application.use_cases.capture_sds_snapshots import (
    CaptureSdsSnapshots,
)
from src.modules.analisis_log_hp.presentation.dependencies import (
    get_error_code_repo,
    get_hp_portal_gateway,
    get_saved_analysis_repo,
    get_telemetry_repo,
)
from src.shared.infrastructure.database.session import get_sessionmaker

logger = logging.getLogger(__name__)


async def _snapshot_task(interval_minutes: int) -> None:
    logger.info("analisis_log_hp_snapshot: iniciando (intervalo %d min)", interval_minutes)
    while True:
        try:
            factory = get_sessionmaker()
            async with factory() as session:
                uc = CaptureSdsSnapshots(
                    repo=get_saved_analysis_repo(session),
                    telemetry=get_telemetry_repo(session),
                    error_code_repo=get_error_code_repo(session),
                    portal=get_hp_portal_gateway(),
                )
                results = await uc.execute_all()
                await session.commit()
            ok = sum(1 for r in results if not r.skipped and not r.error)
            skipped = sum(1 for r in results if r.skipped)
            errors = sum(1 for r in results if r.error)
            logger.info(
                "analisis_log_hp_snapshot: OK — equipos=%d ok=%d skipped=%d errors=%d",
                len(results), ok, skipped, errors,
            )
        except Exception as exc:
            logger.error("analisis_log_hp_snapshot: ciclo fallido", exc_info=exc)
        await asyncio.sleep(interval_minutes * 60)


def start_analisis_log_hp_background_jobs(
    interval_minutes: int,
) -> list[asyncio.Task[None]]:
    return [asyncio.create_task(_snapshot_task(interval_minutes))]
