from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class KnownDeviceModel(Base):
    """`cd_status`/`cd_detail`/`cd_checked_at` solo existían vía `ALTER
    TABLE` incremental en el legacy (nunca en el CREATE TABLE original) —
    acá van directo en la tabla desde el día uno."""

    __tablename__ = "known_devices"
    __table_args__ = (
        Index("idx_known_devices_status", "monitor_status"),
        Index("idx_known_devices_last_contact", "last_contact"),
    )

    device_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    serial: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    model: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    zone: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    ip_address: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    monitor_status: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    monitor_name: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    discovery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_contact: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    offline_dismissed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    cd_status: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    cd_detail: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    cd_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
