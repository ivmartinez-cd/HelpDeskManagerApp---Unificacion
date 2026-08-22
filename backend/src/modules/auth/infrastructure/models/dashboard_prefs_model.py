import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class UserDashboardPrefs(Base):
    """Preferencias de Inicio por usuario (ADR-033): una fila por usuario,
    se pisa en cada PUT. `hidden_cards` es una lista JSON de ids de card del
    frontend; el catálogo de ids vive en el frontend, por eso no es FK."""

    __tablename__ = "user_dashboard_prefs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), primary_key=True
    )
    hidden_cards: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    initial_view: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'hoy'")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
