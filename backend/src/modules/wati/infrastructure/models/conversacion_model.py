from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class ConversacionWatiModel(Base):
    """Una fila por número de WhatsApp — reescrita completa en cada
    sincronización (estado derivado, no historial)."""

    __tablename__ = "wati_conversacion"
    __table_args__ = (
        Index(
            "ix_wati_conversacion_esperando",
            "esperando_desde",
            postgresql_where=text("esperando_desde IS NOT NULL"),
        ),
    )

    wa_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ticket_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    operador_nombre: Mapped[str | None] = mapped_column(String(120), nullable=True)
    operador_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ultimo_mensaje_cliente_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    esperando_desde: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ultima_respuesta_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ultimo_bot_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cerrada_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bot_activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    ultimo_texto_cliente: Mapped[str] = mapped_column(
        String(160), nullable=False, server_default=text("''")
    )
    sincronizado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
