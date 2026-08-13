import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class VacacionesAuditLogModel(Base):
    """Log de auditoría del módulo (AuditLog legacy). `metadata` es palabra
    reservada de SQLAlchemy, por eso el atributo se llama `metadata_json`
    aunque la columna conserve el nombre legacy.
    """

    __tablename__ = "vacaciones_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    accion: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    entidad: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    entidad_id: Mapped[str | None] = mapped_column(String(64))
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_user.id", ondelete="SET NULL"),
        index=True,
    )
    metadata_json: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), index=True
    )
