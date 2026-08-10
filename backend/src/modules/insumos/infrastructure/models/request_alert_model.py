from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class RequestAlertModel(Base):
    """Máquina de estados TRIGGERED→ESCALATED→ACKNOWLEDGED|RESOLVED, con
    reapertura RESOLVED→TRIGGERED."""

    __tablename__ = "request_alerts"
    __table_args__ = (Index("idx_request_alerts_state", "state"),)

    hp_request_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(BigInteger)
    customer_name: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    device_serial: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    sku: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    description: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    state: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'TRIGGERED'"))
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
