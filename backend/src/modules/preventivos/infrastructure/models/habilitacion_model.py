import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class HabilitacionPreventivoModel(Base):
    """Marca local de "equipo habilitado para despachar preventivo" (v1 del
    módulo preventivos: nada de esto escribe en Gestión/Siges). FK lógico por
    `siges_maquina_id` — no hay tabla local de máquinas. Las filas
    desactivadas se conservan como historial de auditoría; el índice parcial
    garantiza a lo sumo UNA activa por máquina."""

    __tablename__ = "preventivos_habilitacion"
    __table_args__ = (
        Index(
            "uq_preventivos_habilitacion_activa",
            "siges_maquina_id",
            unique=True,
            postgresql_where=text("activa"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    siges_maquina_id: Mapped[int] = mapped_column(Integer, nullable=False)
    habilitado_por_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False
    )
    habilitado_por_nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    habilitado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    nota: Mapped[str | None] = mapped_column(String(300), nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    deshabilitado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deshabilitado_por: Mapped[str | None] = mapped_column(String(120), nullable=True)
