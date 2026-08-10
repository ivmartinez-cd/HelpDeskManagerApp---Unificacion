from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, PrimaryKeyConstraint, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class DcaMonitorModel(Base):
    __tablename__ = "dca_monitors"
    __table_args__ = (PrimaryKeyConstraint("customer_id", "monitor_name"),)

    customer_id: Mapped[int] = mapped_column(BigInteger)
    monitor_name: Mapped[str] = mapped_column(String)
    online: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    status: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    last_contact: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
