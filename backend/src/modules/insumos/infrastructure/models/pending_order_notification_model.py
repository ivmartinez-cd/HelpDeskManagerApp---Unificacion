from datetime import datetime

from sqlalchemy import BigInteger, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class PendingOrderNotificationModel(Base):
    __tablename__ = "pending_order_notifications"

    hp_request_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    notified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
