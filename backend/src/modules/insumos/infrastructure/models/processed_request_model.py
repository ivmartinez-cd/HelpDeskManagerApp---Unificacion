from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class ProcessedRequestModel(Base):
    """Núcleo de la idempotencia: una fila por `hp_request_id` (ID de la
    solicitud de consumible en HP Insight) que ya se procesó. `status` es
    CREATED/CANCELLED — nunca se borra una fila (ver `delete_processed` en
    el legacy, que en realidad hace un UPDATE de status, no un DELETE)."""

    __tablename__ = "processed_requests"
    __table_args__ = (
        Index("idx_processed_serial_sku", "device_serial", "sku", "created_at"),
        Index("idx_processed_consumable_serial", "consumable_serial"),
    )

    hp_request_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    device_id: Mapped[int | None] = mapped_column(BigInteger)
    device_serial: Mapped[str | None] = mapped_column(String)
    customer_id: Mapped[int | None] = mapped_column(BigInteger)
    sku: Mapped[str | None] = mapped_column(String)
    internal_order_id: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    initial_percent_left: Mapped[int | None] = mapped_column(Integer)
    initial_days_left: Mapped[int | None] = mapped_column(Integer)
    initial_pages_left: Mapped[int | None] = mapped_column(Integer)
    consumable_serial: Mapped[str | None] = mapped_column(String)
    consumable_colour: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
