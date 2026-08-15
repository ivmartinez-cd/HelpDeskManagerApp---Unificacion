from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class ErrorCodeModel(Base):
    __tablename__ = "pi_error_codes"
    __table_args__ = (Index("ix_pi_error_codes_code", "code", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    severity: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    solution_url: Mapped[str | None] = mapped_column(Text)
    solution_content: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
