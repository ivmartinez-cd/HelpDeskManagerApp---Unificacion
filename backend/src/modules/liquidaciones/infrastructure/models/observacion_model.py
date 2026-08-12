import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class ObservacionModel(Base):
    __tablename__ = "observaciones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    liquidacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("liquidaciones.id", ondelete="CASCADE"), nullable=False
    )
    tipo_observacion: Mapped[str] = mapped_column(String, nullable=False)
    severidad: Mapped[str] = mapped_column(String, nullable=False)
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String)
    datos_contexto: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    monto_cobrado: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0.0"))
    monto_esperado: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0.0"))
    diferencia: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0.0"))
    estado: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'pendiente'"))
    regla_codigo: Mapped[str | None] = mapped_column(String)
    fecha_generacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )


class ObservacionIncidenteModel(Base):
    __tablename__ = "observacion_incidentes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    observacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("observaciones.id", ondelete="CASCADE"), nullable=False
    )
    incidente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidentes.id", ondelete="CASCADE"), nullable=False
    )
    rol: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'referencia'"))
