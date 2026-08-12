import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class LiquidacionModel(Base):
    """Sin `ondelete` en `prestador_id` (a diferencia de SPST/Tarifario/TablaKM): borrar
    un prestador con liquidaciones existentes queda bloqueado a propósito — es historial
    de facturación real, no se pierde por una baja administrativa."""

    __tablename__ = "liquidaciones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    prestador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prestadores.id"), nullable=False
    )
    numero_liquidacion: Mapped[str | None] = mapped_column(String)
    periodo: Mapped[str] = mapped_column(String, nullable=False)
    tipo_liquidacion: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'regular'")
    )
    nombre_archivo: Mapped[str | None] = mapped_column(String)
    fecha_importacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    estado: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'abierta'"))
    total_incidentes: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    total_alertas: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    total_importe: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0.0"))
