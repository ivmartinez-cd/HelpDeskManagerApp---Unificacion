import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class MatchingDescarteModel(Base):
    """Candidato de matching N2 (Tabla KM ↔ Siges) rechazado por un operador —
    un rechazo se recuerda: el mismo par no vuelve a proponerse (decisión
    0.4.d del plan de matching de sucursales)."""

    __tablename__ = "matching_descartes_tabla_km"
    __table_args__ = (UniqueConstraint("tabla_km_id", "siges_sucursal_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    tabla_km_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tabla_kms.id", ondelete="CASCADE"), nullable=False
    )
    siges_sucursal_id: Mapped[int] = mapped_column(Integer, nullable=False)
    usuario_email: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
