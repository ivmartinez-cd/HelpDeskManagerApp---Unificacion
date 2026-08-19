from datetime import datetime

from sqlalchemy import ARRAY, DateTime, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class CpmdManualModel(Base):
    __tablename__ = "pi_cpmd_manuals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
