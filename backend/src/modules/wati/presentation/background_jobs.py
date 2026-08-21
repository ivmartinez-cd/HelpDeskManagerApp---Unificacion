"""Job de fondo del módulo wati: `wati_sync` cada N min (settings) sincroniza
el estado de los chats de WhatsApp contra la API de WATI (polling, solo
lectura). Sin WATI_TENANT_ID/WATI_API_TOKEN el gateway lanza
ExternalServiceError en cada ciclo — se loguea y se reintenta en el próximo."""

import asyncio
import logging

from src.modules.wati.presentation.dependencies import build_sync_conversaciones
from src.shared.infrastructure.database.session import get_sessionmaker

logger = logging.getLogger(__name__)


async def _ciclo_sync() -> None:
    factory = get_sessionmaker()
    async with factory() as session:
        resultado = await build_sync_conversaciones(session).execute()
        await session.commit()
    logger.info(
        "wati_sync: OK — revisados=%d esperando=%d descartados=%d",
        resultado.contactos_revisados,
        resultado.esperando,
        resultado.descartados,
    )


async def background_wati_sync_task(interval_minutes: int) -> None:
    logger.info("wati_sync: iniciando (intervalo %d min)", interval_minutes)
    while True:
        try:
            await _ciclo_sync()
        except Exception as exc:
            logger.error("wati_sync: ciclo fallido", exc_info=exc)
        await asyncio.sleep(interval_minutes * 60)


def start_wati_background_jobs(interval_minutes: int) -> list[asyncio.Task[None]]:
    return [asyncio.create_task(background_wati_sync_task(interval_minutes))]
