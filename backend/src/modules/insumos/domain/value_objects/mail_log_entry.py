"""Una fila del registro de mails salientes de la app."""

from dataclasses import dataclass
from datetime import datetime

# Valores de `kind` que escriben los jobs de fondo (poller_alerts, background_jobs).
KIND_BACKUP = "backup"
KIND_POLLER_ALERT = "poller_alert"
KIND_POLLER_RECOVERY = "poller_recovery"
KIND_PENDING_ORDER_ALERT = "pending_order_alert"
KIND_DISPATCH_UNCONFIRMED_ALERT = "dispatch_unconfirmed_alert"
KIND_CLIENT_ORDER_NOTICE = "client_order_notice"


@dataclass(frozen=True)
class MailLogEntry:
    entry_id: int
    kind: str
    recipients: str
    subject: str
    success: bool
    error: str | None
    sent_at: datetime


@dataclass(frozen=True)
class MailMessage:
    """Un mail lógico a punto de salir: el kind con que se va a registrar y el
    contenido. Los destinatarios NO viajan acá — los resuelve quien despacha."""

    kind: str
    subject: str
    body: str


@dataclass(frozen=True)
class MailLogRecord:
    """Una fila de mail_log a punto de escribirse — un envío lógico, no un
    destinatario: `recipients` es el CSV completo y `success` es True solo si
    TODOS los envíos salieron (contrato de lectura heredado del legacy)."""

    kind: str
    recipients: str
    subject: str
    success: bool
    error: str | None = None
