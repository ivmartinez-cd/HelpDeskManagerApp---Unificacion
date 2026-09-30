import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class NotificacionModel(Base):
    __tablename__ = "notificaciones"
    __table_args__ = (Index("ix_notificaciones_audiencia_creada", "audiencia", "creada_en"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    # Única: publicar dos veces el mismo hecho no lo duplica (ON CONFLICT DO NOTHING).
    clave: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    audiencia: Mapped[str] = mapped_column(String, nullable=False)
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(String)
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class NotificacionLecturaModel(Base):
    """Quién leyó qué. La lectura es por usuario: una notificación a una
    audiencia de 10 personas tiene hasta 10 filas acá."""

    __tablename__ = "notificaciones_lecturas"

    notificacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notificaciones.id", ondelete="CASCADE"),
        primary_key=True,
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), primary_key=True
    )
    leida_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
