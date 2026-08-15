import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class TelemetryModel(Base):
    __tablename__ = "pi_device_telemetry_events"
    __table_args__ = (
        Index("ix_pi_telemetry_serial_time", "device_serial", "event_time"),
        Index("ix_pi_telemetry_serial_code", "device_serial", "code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    device_serial: Mapped[str] = mapped_column(String, nullable=False)
    saved_analysis_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    code: Mapped[str] = mapped_column(String, nullable=False)
    classification: Mapped[str | None] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'INFO'"))
    occurrences: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    counter: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
