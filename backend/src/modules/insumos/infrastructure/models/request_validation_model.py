from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Double, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class RequestValidationModel(Base):
    """Ventana de validación para solicitudes que llegan en 0% exacto (no
    solo "bajo") — no es idempotencia, pero toca la misma tabla/lock que la
    creación de pedidos."""

    __tablename__ = "request_validations"
    __table_args__ = (Index("idx_request_validations_due", "status", "deadline_at"),)

    hp_request_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    device_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    device_serial: Mapped[str] = mapped_column(String, nullable=False)
    sku: Mapped[str] = mapped_column(String, nullable=False)
    initial_percent_left: Mapped[float | None] = mapped_column(Double)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'PENDING'"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    swap_note: Mapped[str | None] = mapped_column(String)
    swap_checked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    diagnosis_headline: Mapped[str | None] = mapped_column(String)
    diagnosis_detail: Mapped[str | None] = mapped_column(String)
