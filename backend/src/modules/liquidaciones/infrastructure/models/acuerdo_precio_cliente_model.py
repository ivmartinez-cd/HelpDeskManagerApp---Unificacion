import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class AcuerdoPrecioClienteModel(Base):
    __tablename__ = "acuerdos_precio_cliente"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    prestador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prestadores.id", ondelete="CASCADE"), nullable=False
    )
    empresa_nombre: Mapped[str] = mapped_column(String, nullable=False)
    tipo_servicio: Mapped[str | None] = mapped_column(String)
    factor: Mapped[float | None] = mapped_column(Float)
    precio_fijo: Mapped[float | None] = mapped_column(Float)
    motivo: Mapped[str] = mapped_column(String, nullable=False)
    vigencia_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vigencia_hasta: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
