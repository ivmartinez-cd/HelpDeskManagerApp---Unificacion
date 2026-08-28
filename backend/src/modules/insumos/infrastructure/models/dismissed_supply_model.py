from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class DismissedSupplyModel(Base):
    """Pedido despachado sin confirmar entrega, descartado a mano — PK por supply_id
    (no hp_request_id, que HP SDS puede reemitir). hp_request_id NULL = descarte
    permanente, no se revierte solo (ver domain/entities/dismissed_supply.py)."""

    __tablename__ = "dismissed_supplies"

    supply_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    device_serial: Mapped[str] = mapped_column(String, nullable=False)
    hp_request_id: Mapped[int | None] = mapped_column(BigInteger)
    dismissed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
