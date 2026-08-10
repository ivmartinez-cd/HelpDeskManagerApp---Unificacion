from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class SupplyStatusHistoryModel(Base):
    """Nunca se poda (a diferencia de supply_serial_cache) — es el dato que
    sostiene las métricas históricas de estado."""

    __tablename__ = "supply_status_history"
    __table_args__ = (
        UniqueConstraint("supply_id", "estado"),
        Index("idx_supply_history_seen", "first_seen_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    supply_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
