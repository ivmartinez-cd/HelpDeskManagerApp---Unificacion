import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class ReporteAppModel(Base):
    """Error o mejora que carga un usuario desde el botón "Reportar" del header.
    Circuito: `nuevo` -> Claude deja diagnóstico y propuesta en `nota` por el
    servidor MCP (`scripts/mcp/reportes_app_mcp.py`) -> `propuesto` -> el
    superadmin aprueba, pide cambios (vuelve a `nuevo`) o descarta desde el
    panel, con `respuesta` -> Claude trabaja solo los `aprobado`."""

    __tablename__ = "reportes_app"
    __table_args__ = (
        CheckConstraint("tipo IN ('error', 'mejora')", name="ck_reportes_app_tipo"),
        CheckConstraint(
            "estado IN ('nuevo', 'propuesto', 'aprobado', 'en_curso', 'resuelto', 'descartado')",
            name="ck_reportes_app_estado",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    detalle: Mapped[str] = mapped_column(Text, nullable=False)
    ruta: Mapped[str] = mapped_column(String, nullable=False)
    # Nombre de archivo dentro de `var/reportes_app/fotos`, no un path.
    foto: Mapped[str | None] = mapped_column(String)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL")
    )
    estado: Mapped[str] = mapped_column(String, nullable=False, server_default="nuevo")
    nota: Mapped[str | None] = mapped_column(Text)
    respuesta: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    actualizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
