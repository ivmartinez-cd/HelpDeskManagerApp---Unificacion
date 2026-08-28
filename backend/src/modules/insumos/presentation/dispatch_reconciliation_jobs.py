"""Dos jobs de fondo separados de background_jobs.py porque ese archivo ya está en el
tamaño máximo (§4):

1. Aviso a logística (dedup) cuando sale una solicitud nueva para un equipo que ya
   tiene un pedido despachado sin confirmar entrega (ver dispatch_unconfirmed_alert.py).
2. UNIGNORE automático: descartes temporales (dismiss_request con supply_id, no
   ignore_request) cuyo supply llegó a un estado final en Canal Directo — sin esto, la
   alerta quedaría muda para siempre aunque el equipo vuelva a necesitar insumo (ver
   dismiss_reconciliation.py).
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.dtos.request_rows import RequestRow
from src.modules.insumos.application.jobs.dismiss_reconciliation import (
    build_unignore_comment,
    find_supplies_ready_to_unignore,
)
from src.modules.insumos.application.jobs.dispatch_unconfirmed_alert import (
    build_dispatch_unconfirmed_mail,
    find_dispatch_unconfirmed_due,
)
from src.modules.insumos.application.jobs.mail_delivery import send_mail_to_all
from src.modules.insumos.domain.entities.dismissed_supply import DismissedSupply
from src.modules.insumos.domain.repositories.dismissed_supply_repository import (
    DismissedSupplyRepository,
)
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway
from src.modules.insumos.domain.repositories.mailer import Mailer
from src.modules.insumos.domain.value_objects.insumos_settings import (
    logistics_recipients,
    settings_from_raw,
)
from src.modules.insumos.domain.value_objects.mail_log_entry import (
    KIND_DISPATCH_UNCONFIRMED_ALERT,
    MailMessage,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_dismissed_supply_repository import (  # noqa: E501
    SqlAlchemyDismissedSupplyRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_dispatch_unconfirmed_notification_repository import (  # noqa: E501
    SqlAlchemyDispatchUnconfirmedNotificationRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_insumos_settings_repository import (  # noqa: E501
    SqlAlchemyInsumosSettingsRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_mail_log_repository import (
    SqlAlchemyMailLogRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_supply_cache_repository import (
    SqlAlchemySupplyCacheRepository,
)
from src.modules.insumos.presentation.dependencies.requests import build_list_requests
from src.modules.insumos.presentation.wiring import get_insight_gateway
from src.shared.infrastructure.database.session import get_sessionmaker

logger = logging.getLogger(__name__)


async def background_dispatch_unconfirmed_task(mailer: Mailer, interval_minutes: int = 15) -> None:
    logger.info("dispatch_unconfirmed_alert: iniciando (intervalo %d min)", interval_minutes)
    while True:
        try:
            await _run_dispatch_unconfirmed_cycle(mailer)
        except Exception as exc:
            logger.error("dispatch_unconfirmed_alert: ciclo fallido", exc_info=exc)
        await asyncio.sleep(interval_minutes * 60)


async def _run_dispatch_unconfirmed_cycle(mailer: Mailer) -> None:
    factory = get_sessionmaker()
    async with factory() as session:
        raw_settings = await SqlAlchemyInsumosSettingsRepository(session).get_all()
        recipients = logistics_recipients(settings_from_raw(raw_settings))
        if not recipients:
            return
        rows = await build_list_requests(session).execute(None)
        notifications = SqlAlchemyDispatchUnconfirmedNotificationRepository(session)
        already = await notifications.get_notified_ids([r.request_id for r in rows])
        due = find_dispatch_unconfirmed_due(rows, already)
        if not due:
            return
        await _send_dispatch_alert(session, mailer, recipients, due, notifications)
        await session.commit()
    logger.info("dispatch_unconfirmed_alert: %d solicitud(es) notificada(s)", len(due))


async def _send_dispatch_alert(
    session: AsyncSession,
    mailer: Mailer,
    recipients: list[str],
    due: list[RequestRow],
    notifications: SqlAlchemyDispatchUnconfirmedNotificationRepository,
) -> None:
    subject, body = build_dispatch_unconfirmed_mail(due)
    message = MailMessage(kind=KIND_DISPATCH_UNCONFIRMED_ALERT, subject=subject, body=body)
    delivery = await send_mail_to_all(mailer, recipients, message)
    await SqlAlchemyMailLogRepository(session).record(delivery.log)
    if delivery.delivered > 0:
        await notifications.mark_notified([r.request_id for r in due])


async def background_dismiss_reconciliation_task(interval_minutes: int = 15) -> None:
    logger.info("dismiss_reconciliation: iniciando (intervalo %d min)", interval_minutes)
    while True:
        try:
            await _run_dismiss_reconciliation_cycle()
        except Exception as exc:
            logger.error("dismiss_reconciliation: ciclo fallido", exc_info=exc)
        await asyncio.sleep(interval_minutes * 60)


async def _run_dismiss_reconciliation_cycle() -> None:
    factory = get_sessionmaker()
    async with factory() as session:
        dismissed = SqlAlchemyDismissedSupplyRepository(session)
        pending = await dismissed.get_pending_unignore()
        if not pending:
            return
        statuses = await SqlAlchemySupplyCacheRepository(session).get_statuses_batch(
            [d.supply_id for d in pending]
        )
        ready = find_supplies_ready_to_unignore(pending, statuses)
        insight = get_insight_gateway()
        for entry in ready:
            await _unignore_one(insight, dismissed, entry, statuses[entry.supply_id])
        await session.commit()
    if ready:
        logger.info("dismiss_reconciliation: %d pedido(s) reactivado(s) (UNIGNORE)", len(ready))


async def _unignore_one(
    insight: InsightGateway,
    dismissed: DismissedSupplyRepository,
    entry: DismissedSupply,
    estado: str,
) -> None:
    assert entry.hp_request_id is not None  # ver DismissedSupplyRepository.get_pending_unignore
    try:
        await insight.update_consumable_request(
            request_id=entry.hp_request_id,
            status_update="UNIGNORE",
            comment=build_unignore_comment(entry.supply_id, estado),
        )
        await dismissed.clear(entry.supply_id)
    except Exception:
        _log_unignore_failure(entry)


def _log_unignore_failure(entry: DismissedSupply) -> None:
    # No limpiar el descarte si UNIGNORE falló — se reintenta en el próximo ciclo en
    # vez de dejar la solicitud muda para siempre.
    logger.exception(
        "dismiss_reconciliation: no se pudo mandar UNIGNORE para la solicitud %s (pedido %s)",
        entry.hp_request_id,
        entry.supply_id,
    )
