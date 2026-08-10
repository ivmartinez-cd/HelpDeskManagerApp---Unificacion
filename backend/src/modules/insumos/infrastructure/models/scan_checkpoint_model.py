from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class ScanCheckpointModel(Base):
    """Key-value; en la práctica una sola fila real
    (`key='supply_scan_max_id'`)."""

    __tablename__ = "scan_checkpoint"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
