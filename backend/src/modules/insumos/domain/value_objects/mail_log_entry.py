"""Una fila del registro de mails salientes de la app."""

from dataclasses import dataclass
from datetime import datetime

# Valores de `kind` que escriben los jobs de fondo (todavía sin portar).
KIND_BACKUP = "backup"
KIND_POLLER_ALERT = "poller_alert"
KIND_POLLER_RECOVERY = "poller_recovery"
KIND_PENDING_ORDER_ALERT = "pending_order_alert"


@dataclass(frozen=True)
class MailLogEntry:
    entry_id: int
    kind: str
    recipients: str
    subject: str
    success: bool
    error: str | None
    sent_at: datetime
