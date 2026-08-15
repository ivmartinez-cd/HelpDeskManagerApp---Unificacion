import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class SavedAnalysisModel(Base):
    __tablename__ = "pi_saved_analyses"
    __table_args__ = (Index("ix_pi_saved_analyses_created_at", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    equipment_identifier: Mapped[str | None] = mapped_column(String)
    incidents: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'"))
    global_severity: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'INFO'")
    )
    ai_diagnosis: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
