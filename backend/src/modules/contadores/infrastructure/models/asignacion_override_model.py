import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.base import Base


class AsignacionOverrideModel(Base):
    """Override temporal de asignación (ver ADR-013) — no reemplaza los
    eventos sincronizados ni `contadores_operadores`, se resuelve en lectura.
    `alcance_total=True` cubre todos los clientes del operador ausente; si es
    `False`, el alcance está en las filas de
    `contadores_asignacion_override_cliente`. `operador_ausente_id`/
    `operador_reemplazante_id` son usernames de Gestión, sin FK a
    `contadores_operadores` (esa tabla se poda en cada sync)."""

    __tablename__ = "contadores_asignacion_override"
    __table_args__ = (
        CheckConstraint("vigente_desde <= vigente_hasta", name="ck_calendar_override_rango"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    operador_ausente_id: Mapped[str] = mapped_column(String, nullable=False)
    operador_reemplazante_id: Mapped[str] = mapped_column(String, nullable=False)
    vigente_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vigente_hasta: Mapped[date] = mapped_column(Date, nullable=False)
    alcance_total: Mapped[bool] = mapped_column(Boolean, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVA")
    motivo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    clientes: Mapped[list["AsignacionOverrideClienteModel"]] = relationship(
        "AsignacionOverrideClienteModel", back_populates="override", cascade="all, delete-orphan"
    )


class AsignacionOverrideClienteModel(Base):
    """Alcance por cliente puntual de un override (solo tiene filas cuando
    `alcance_total=False` en el override padre)."""

    __tablename__ = "contadores_asignacion_override_cliente"

    override_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contadores_asignacion_override.id", ondelete="CASCADE"),
        primary_key=True,
    )
    cliente: Mapped[str] = mapped_column(String(200), primary_key=True)

    override: Mapped["AsignacionOverrideModel"] = relationship(
        "AsignacionOverrideModel", back_populates="clientes"
    )
