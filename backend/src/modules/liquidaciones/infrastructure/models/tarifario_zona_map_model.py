import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class TarifarioZonaMapModel(Base):
    __tablename__ = "tarifario_zona_maps"
    __table_args__ = (
        UniqueConstraint(
            "prestador_id", "descripcion_siges", name="uq_tarifario_zona_maps_prestador_desc"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    prestador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prestadores.id", ondelete="CASCADE"), nullable=False
    )
    descripcion_siges: Mapped[str] = mapped_column(String, nullable=False)
    # NULL = mapeada a la tarifa genérica (sin SPST específico).
    spst_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spsts.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
