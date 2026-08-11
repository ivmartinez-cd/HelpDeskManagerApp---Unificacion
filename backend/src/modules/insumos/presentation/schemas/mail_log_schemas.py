"""Schema de GET /api/insumos/mail-log — mismo contrato snake_case que el legacy
(routers/mail_log.py::MailLogRow), con `sent_at` ISO en vez del string de SQLite."""

from datetime import datetime

from pydantic import BaseModel

from src.modules.insumos.domain.value_objects.mail_log_entry import MailLogEntry


class MailLogRowOut(BaseModel):
    id: int
    kind: str
    recipients: str
    subject: str
    success: bool
    error: str | None = None
    sent_at: datetime

    @classmethod
    def from_entry(cls, entry: MailLogEntry) -> "MailLogRowOut":
        return cls(
            id=entry.entry_id,
            kind=entry.kind,
            recipients=entry.recipients,
            subject=entry.subject,
            success=entry.success,
            error=entry.error,
            sent_at=entry.sent_at,
        )
