import uuid
from datetime import UTC, datetime

from sqlalchemy import Date, DateTime, Float, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class CalendarEventModel(Base):
    """Copia local de un evento de facturación de Gestión. `operador_id` es
    el username que Gestión estampa en el campo `operador` del propio evento
    (ver GestionPlanificacionClient / SyncCalendarEventsUseCase).
    `event_date` es `start` truncado a fecha, para poder filtrar por rango
    sin parsear el string en cada consulta."""

    __tablename__ = "contadores_calendar_events"
    __table_args__ = (
        UniqueConstraint(
            "gestion_event_id", "operador_id", name="uq_calendar_event_gestion_operador"
        ),
        Index("ix_calendar_event_date", "event_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    gestion_event_id: Mapped[str] = mapped_column(String, nullable=False)
    operador_id: Mapped[str] = mapped_column(String, nullable=False)
    event_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    start: Mapped[str] = mapped_column(String, nullable=False)
    all_day: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    background_color: Mapped[str | None] = mapped_column(String)
    border_color: Mapped[str | None] = mapped_column(String)
    type: Mapped[str | None] = mapped_column(String)
    tittle_tooltip: Mapped[str | None] = mapped_column(String)
    content_tooltip: Mapped[str | None] = mapped_column(Text)
    string_tipo_evento: Mapped[str | None] = mapped_column(String)
    cliente: Mapped[str | None] = mapped_column(String)
    vendedor: Mapped[str | None] = mapped_column(String)
    fecha_entrega: Mapped[str | None] = mapped_column(String)
    fecha_entrega_deseada: Mapped[str | None] = mapped_column(String)
    sucursal_entrega: Mapped[str | None] = mapped_column(String)
    sucursal_instalacion: Mapped[str | None] = mapped_column(String)
    sucursal_despacho: Mapped[str | None] = mapped_column(String)
    contacto_entrega: Mapped[str | None] = mapped_column(String)
    contacto_instalacion: Mapped[str | None] = mapped_column(String)
    bultos: Mapped[float | None] = mapped_column(Float)
    costo_seguro: Mapped[str | None] = mapped_column(String)
    costo_recambio: Mapped[str | None] = mapped_column(String)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=lambda: datetime.now(UTC),
    )
