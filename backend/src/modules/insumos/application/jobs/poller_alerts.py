"""Vigilancia del poller de insumos — alerta por mail cuando falla N veces consecutivas.

Una sola alerta por caída (no un mail por ciclo): el mail sale al llegar al
umbral y no antes; la recuperación se avisa también con un único mail. Mismo
comportamiento que el legacy (alerts.py de SDSInsumos).
"""

import logging

from src.modules.insumos.domain.repositories.mail_dispatcher import MailDispatcher
from src.modules.insumos.domain.value_objects.mail_log_entry import (
    KIND_POLLER_ALERT,
    KIND_POLLER_RECOVERY,
    MailMessage,
)

logger = logging.getLogger(__name__)


class PollerAlerts:
    def __init__(
        self,
        dispatcher: MailDispatcher,
        threshold: int = 3,
    ) -> None:
        self._dispatcher = dispatcher
        self._threshold = threshold
        self._consecutive_failures = 0
        self._outage_notified = False

    async def record_failure(self, error_summary: str) -> None:
        self._consecutive_failures += 1
        if self._outage_notified or self._consecutive_failures < self._threshold:
            return
        self._outage_notified = True
        logger.error(
            "poller_alerts: umbral de %d fallos consecutivos alcanzado — enviando aviso",
            self._consecutive_failures,
        )
        subject = "[HelpDesk Manager] El poller de insumos no responde"
        body = (
            f"El poller de insumos falló {self._consecutive_failures} veces consecutivas.\n\n"
            f"Último error: {error_summary}\n\n"
            "Verificar credenciales de Insight y conectividad de red."
        )
        await self._dispatcher.dispatch(
            MailMessage(kind=KIND_POLLER_ALERT, subject=subject, body=body)
        )

    async def record_success(self) -> None:
        if self._outage_notified:
            logger.info("poller_alerts: recuperación — enviando aviso")
            await self._dispatcher.dispatch(
                MailMessage(
                    kind=KIND_POLLER_RECOVERY,
                    subject="[HelpDesk Manager] El poller de insumos se recuperó",
                    body="El poller de insumos volvió a funcionar correctamente.",
                )
            )
        self._consecutive_failures = 0
        self._outage_notified = False
