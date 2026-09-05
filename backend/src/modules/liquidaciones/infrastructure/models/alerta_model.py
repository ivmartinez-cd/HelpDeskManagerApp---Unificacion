import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class AlertaModel(Base):
    __tablename__ = "alertas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    incidente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidentes.id", ondelete="CASCADE"), nullable=False
    )
    liquidacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("liquidaciones.id", ondelete="CASCADE"), nullable=False
    )
    tipo_alerta: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String)
    datos_contexto: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    riesgo: Mapped[float] = mapped_column(Float, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'pendiente'"))
    justificacion: Mapped[str | None] = mapped_column(String)
    incidente_relacionado_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidentes.id", ondelete="SET NULL")
    )
    fecha_generacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    # Ex `Observacion` (ver `domain/entities/alerta.py`) — hoy solo lo genera
    # ALT005 agrupando por corredor; los incidentes del grupo viven en
    # `alerta_incidentes` (`AlertaIncidenteModel`).
    es_grupo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    monto_cobrado: Mapped[float | None] = mapped_column(Float)
    monto_esperado: Mapped[float | None] = mapped_column(Float)
    diferencia: Mapped[float | None] = mapped_column(Float)


class AlertaIncidenteModel(Base):
    """Incidentes que integran una alerta agrupada (`es_grupo=True`) — ex
    `observacion_incidentes`."""

    __tablename__ = "alerta_incidentes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    alerta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alertas.id", ondelete="CASCADE"), nullable=False
    )
    incidente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidentes.id", ondelete="CASCADE"), nullable=False
    )
    rol: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'referencia'"))
