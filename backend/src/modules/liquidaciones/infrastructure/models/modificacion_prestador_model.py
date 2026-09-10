import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class ModificacionPrestadorModel(Base):
    __tablename__ = "modificaciones_prestador"
    __table_args__ = (
        Index("ix_modificaciones_prestador_liquidacion_id", "liquidacion_id"),
        Index(
            "ix_modificaciones_prestador_no_vistas",
            "vista_en",
            postgresql_where=text("vista_en IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    # Sin FK al incidente a propósito — una `baja` tiene que sobrevivir al borrado
    # del incidente (ver `domain/entities/modificacion_prestador.py`).
    liquidacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("liquidaciones.id", ondelete="CASCADE"), nullable=False
    )
    numero_incidente: Mapped[str] = mapped_column(String, nullable=False)
    tipo_cambio: Mapped[str] = mapped_column(String, nullable=False)
    campo: Mapped[str | None] = mapped_column(String)
    valor_anterior: Mapped[str | None] = mapped_column(String)
    valor_nuevo: Mapped[str | None] = mapped_column(String)
    detectada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    vista_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
