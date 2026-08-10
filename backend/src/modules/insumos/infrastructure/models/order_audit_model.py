from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class OrderAuditModel(Base):
    """Historial permanente, nunca se borra — fuente de todas las
    estadísticas. Índice `(hp_request_id)` es nuevo respecto al legacy: no
    lo tenía, pero `count_created_today` filtra por esa columna (hallazgo
    de la caracterización)."""

    __tablename__ = "order_audit"
    __table_args__ = (
        Index("idx_audit_created", "created_at"),
        Index("idx_audit_customer_created", "customer_id", "created_at"),
        Index("idx_audit_hp_request_id", "hp_request_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event: Mapped[str] = mapped_column(String, nullable=False)
    hp_request_id: Mapped[int | None] = mapped_column(BigInteger)
    device_id: Mapped[int | None] = mapped_column(BigInteger)
    customer_id: Mapped[int | None] = mapped_column(BigInteger)
    customer_name: Mapped[str | None] = mapped_column(String)
    device_serial: Mapped[str | None] = mapped_column(String)
    sku: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    internal_order_id: Mapped[str | None] = mapped_column(String)
    order_type: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'supply'"))
    detail: Mapped[str | None] = mapped_column(String)
    dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    hp_request_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    initial_percent_left: Mapped[int | None] = mapped_column(Integer)
    initial_days_left: Mapped[int | None] = mapped_column(Integer)
    initial_pages_left: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
