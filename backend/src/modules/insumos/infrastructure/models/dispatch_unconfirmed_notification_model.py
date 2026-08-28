from datetime import datetime

from sqlalchemy import BigInteger, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class DispatchUnconfirmedNotificationModel(Base):
    """Dedup del aviso a logística de "solicitud nueva con pedido despachado sin
    confirmar entrega" — una fila por hp_request_id ya avisado."""

    __tablename__ = "dispatch_unconfirmed_notifications"

    hp_request_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    notified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
