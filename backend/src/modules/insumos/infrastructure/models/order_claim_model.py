from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class OrderClaimModel(Base):
    """Mecanismo de idempotencia que reemplaza a `KeyedLock` (ver
    domain/services/claimed_order_creation.py). El índice único parcial
    (`status='IN_PROGRESS'`) es lo que hace atómico el "reclamar" — se crea
    acá para que quede junto al modelo, aunque el índice `WHERE` real lo
    define la migración."""

    __tablename__ = "order_claim"
    __table_args__ = (
        Index(
            "uq_order_claim_in_progress",
            "device_serial",
            "sku",
            unique=True,
            postgresql_where=text("status = 'IN_PROGRESS'"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_serial: Mapped[str] = mapped_column(String, nullable=False)
    sku: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'IN_PROGRESS'")
    )
    claimed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
