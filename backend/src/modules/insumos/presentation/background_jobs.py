"""Jobs de fondo del módulo insumos — asyncio.create_task, sin APScheduler.

Notas de diseño:
- El backup de BD del legacy (SQLite) no tiene equivalente 1:1 en Postgres; ese
  job se omite conscientemente. Postgres corre con su propia infraestructura de
  backup (pg_dump, streaming replication, etc.).
- La auto-carga (maybe_auto_load del legacy, ver AutoLoadRequests) corre en el mismo
  ciclo del poller, después del sync de inventario — mismo orden que el legacy — pero
  con su propio try/except: un fallo de auto-carga no debe ocultar si el sync de
  inventario funcionó, y viceversa.
- DISABLE_BACKGROUND_JOBS=true desactiva todos los jobs (útil en CI o cuando se
  corren múltiples instancias y solo una debe ejecutar los jobs).
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.dtos.pending_orders import PendingOrderRow
from src.modules.insumos.application.jobs.mail_delivery import send_mail_to_all
from src.modules.insumos.application.jobs.poller_alerts import PollerAlerts
from src.modules.insumos.application.use_cases.pending_order_alert import (
    build_pending_alert_mail,
    find_orders_due_for_alert,
)
from src.modules.insumos.domain.repositories.mailer import Mailer
from src.modules.insumos.domain.value_objects.insumos_settings import (
    logistics_recipients,
    settings_from_raw,
)
from src.modules.insumos.domain.value_objects.mail_log_entry import (
    KIND_PENDING_ORDER_ALERT,
    MailMessage,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_insumos_settings_repository import (  # noqa: E501
    SqlAlchemyInsumosSettingsRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_mail_log_repository import (
    SqlAlchemyMailLogRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_pending_order_notification_repository import (  # noqa: E501
    SqlAlchemyPendingOrderNotificationRepository,
)
from src.modules.insumos.presentation.dependencies.alerts import build_sync_pending_alerts
from src.modules.insumos.presentation.dependencies.new_devices import build_sync_new_devices
from src.modules.insumos.presentation.dependencies.offline_devices import (
    build_verify_offline_devices,
)
from src.modules.insumos.presentation.dependencies.requests import (
    build_auto_load_requests,
    build_list_pending_orders,
)
from src.shared.infrastructure.database.session import get_sessionmaker

logger = logging.getLogger(__name__)

# Equipos offline: sin límite real — el job procesa todo lo pendiente cada vez.
_OFFLINE_VERIFY_LIMIT = 500
# Hora UTC en que corre el job diario de equipos offline.
_OFFLINE_CHECK_HOUR_UTC = 3


def seconds_until_next_hour(hour: int) -> float:
    """Segundos hasta la próxima ocurrencia de `hour:00` UTC."""
    now = datetime.now(UTC)
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def background_poller_task(
    poller_alerts: PollerAlerts, interval_minutes: int
) -> None:
    logger.info("poller: iniciando (intervalo %d min)", interval_minutes)
    while True:
        await _run_sync_cycle(poller_alerts)
        await _run_autoload_cycle()
        await asyncio.sleep(interval_minutes * 60)


async def _run_sync_cycle(poller_alerts: PollerAlerts) -> None:
    try:
        factory = get_sessionmaker()
        async with factory() as session:
            result = await build_sync_new_devices(session).execute()
            await session.commit()
        await poller_alerts.record_success()
        logger.info(
            "poller: sync OK — %d nuevos equipos, %d podados",
            len(result.new_device_ids),
            result.pruned,
        )
    except Exception as exc:
        logger.error("poller: ciclo de sync fallido", exc_info=exc)
        await poller_alerts.record_failure(str(exc))


async def _run_autoload_cycle() -> None:
    """Auto-carga (maybe_auto_load del legacy) — try/except propio: un fallo acá no
    debe ocultar si el sync de inventario funcionó (ver _run_sync_cycle)."""
    try:
        factory = get_sessionmaker()
        async with factory() as session:
            result = await build_auto_load_requests(session).execute()
            await session.commit()
        logger.info(
            "poller: auto_load OK — considerados=%d creados=%d saltados=%d",
            result.considered,
            result.created,
            result.skipped,
        )
    except Exception as exc:
        logger.error("poller: ciclo de auto_load fallido", exc_info=exc)


async def background_offline_check_task() -> None:
    logger.info("offline_check: iniciando (diario @ %02d:00 UTC)", _OFFLINE_CHECK_HOUR_UTC)
    while True:
        await asyncio.sleep(seconds_until_next_hour(_OFFLINE_CHECK_HOUR_UTC))
        try:
            factory = get_sessionmaker()
            async with factory() as session:
                use_case = await build_verify_offline_devices(session)
                result = await use_case.execute(limit=_OFFLINE_VERIFY_LIMIT)
                await session.commit()
            logger.info(
                "offline_check: OK — checked=%d remaining=%d errores=%d",
                result.checked,
                result.remaining,
                result.errores,
            )
        except Exception as exc:
            logger.error("offline_check: ciclo fallido", exc_info=exc)


async def background_alert_task(interval_minutes: int = 15) -> None:
    logger.info("alert_sync: iniciando (intervalo %d min)", interval_minutes)
    while True:
        try:
            factory = get_sessionmaker()
            async with factory() as session:
                count = await build_sync_pending_alerts(session).execute()
                await session.commit()
            logger.debug("alert_sync: OK — %d solicitudes pendientes", count)
        except Exception as exc:
            logger.error("alert_sync: ciclo fallido", exc_info=exc)
        await asyncio.sleep(interval_minutes * 60)


async def background_pending_alert_task(mailer: Mailer, interval_minutes: int = 15) -> None:
    logger.info("pending_alert: iniciando (intervalo %d min)", interval_minutes)
    while True:
        try:
            await _run_pending_alert_cycle(mailer)
        except Exception as exc:
            logger.error("pending_alert: ciclo fallido", exc_info=exc)
        await asyncio.sleep(interval_minutes * 60)


@dataclass(frozen=True)
class _PendingAlert:
    recipients: list[str]
    rows: list[PendingOrderRow]
    threshold_days: int


async def _send_pending_alert(
    session: AsyncSession, mailer: Mailer, alert: _PendingAlert
) -> None:
    subject, body = build_pending_alert_mail(alert.rows, alert.threshold_days)
    delivery = await send_mail_to_all(
        mailer,
        alert.recipients,
        MailMessage(kind=KIND_PENDING_ORDER_ALERT, subject=subject, body=body),
    )
    await SqlAlchemyMailLogRepository(session).record(delivery.log)
    if delivery.delivered == 0:
        # ARREGLO DE BUG: el legacy no marcaba si el envío fallaba — marcarlo
        # igual perdía el aviso para siempre. Se reintenta en el ciclo siguiente.
        logger.error(
            "pending_alert: ningún destinatario recibió el aviso — %s", delivery.log.error
        )
        return
    await SqlAlchemyPendingOrderNotificationRepository(session).mark_notified(
        [r.hp_request_id for r in alert.rows]
    )


async def _find_pending_alert(session: AsyncSession) -> _PendingAlert | None:
    raw_settings = await SqlAlchemyInsumosSettingsRepository(session).get_all()
    settings = settings_from_raw(raw_settings)
    recipients = logistics_recipients(settings)
    if not recipients:
        logger.debug("pending_alert: sin destinatarios configurados, se omite")
        return None
    rows = await build_list_pending_orders(session).execute(
        customer_id=None, include_delivered=False
    )
    hp_ids = [r.hp_request_id for r in rows]
    already_notified = await SqlAlchemyPendingOrderNotificationRepository(
        session
    ).get_notified_ids(hp_ids)
    due = find_orders_due_for_alert(rows, settings.threshold_urgent, already_notified)
    if not due:
        return None
    return _PendingAlert(
        recipients=recipients, rows=due, threshold_days=settings.threshold_urgent
    )


async def _run_pending_alert_cycle(mailer: Mailer) -> None:
    factory = get_sessionmaker()
    async with factory() as session:
        alert = await _find_pending_alert(session)
        if alert is None:
            return
        await _send_pending_alert(session, mailer, alert)
        await session.commit()
    logger.info("pending_alert: %d pedido(s) considerados", len(alert.rows))


def start_background_jobs(mailer: Mailer, poller_alerts: PollerAlerts, interval_minutes: int) -> list[asyncio.Task[None]]:  # noqa: E501
    return [
        asyncio.create_task(background_poller_task(poller_alerts, interval_minutes)),
        asyncio.create_task(background_offline_check_task()),
        asyncio.create_task(background_alert_task()),
        asyncio.create_task(background_pending_alert_task(mailer)),
    ]
