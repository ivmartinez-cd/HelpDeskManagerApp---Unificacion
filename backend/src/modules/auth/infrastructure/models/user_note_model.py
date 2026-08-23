import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class UserNoteModel(Base):
    """Nota personal de Inicio: una fila por usuario que se pisa en cada PUT
    (ADR-033, addendum nota). Sin índice sobre `content`: habilita HOT updates
    y el texto TOASTea/comprime solo por encima de ~2 KB."""

    __tablename__ = "user_note"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), primary_key=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
