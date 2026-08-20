import uuid
from datetime import UTC, date, datetime, time

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Time,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.base import Base


class TurnoGrillaVarianteModel(Base):
    """Grilla alternativa de turnos con vigencia (modo vacaciones, ADR-025).
    No referencia `turno_slot`: sus franjas son filas propias en
    `turno_grilla_variante_slot`. `estado` es String + CHECK (mismo criterio
    que `turno_asignacion_override.estado`), sin tipo enum de Postgres."""

    __tablename__ = "turno_grilla_variante"
    __table_args__ = (
        CheckConstraint("desde <= hasta", name="ck_grilla_variante_rango_valido"),
        CheckConstraint(
            "estado IN ('ACTIVA', 'CANCELADA')", name="ck_grilla_variante_estado"
        ),
        Index("ix_grilla_variante_estado_vigencia", "estado", "desde", "hasta"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    motivo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    origen_texto: Mapped[str | None] = mapped_column(String(200), nullable=True)
    desde: Mapped[date] = mapped_column(Date, nullable=False)
    hasta: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVA")
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=lambda: datetime.now(UTC),
    )

    slots: Mapped[list["TurnoGrillaVarianteSlotModel"]] = relationship(
        "TurnoGrillaVarianteSlotModel",
        back_populates="variante",
        cascade="all, delete-orphan",
        order_by="TurnoGrillaVarianteSlotModel.sort_order",
    )


class TurnoGrillaVarianteSlotModel(Base):
    __tablename__ = "turno_grilla_variante_slot"
    __table_args__ = (
        CheckConstraint("hora_inicio < hora_fin", name="ck_grilla_variante_slot_horas"),
        Index("ix_grilla_variante_slot_variante", "variante_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    variante_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("turno_grilla_variante.id", ondelete="CASCADE"),
        nullable=False,
    )
    casilla_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("turno_casilla.id", ondelete="CASCADE"), nullable=False
    )
    dia_semana: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 0=Mon .. 6=Sun
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    variante: Mapped["TurnoGrillaVarianteModel"] = relationship(
        "TurnoGrillaVarianteModel", back_populates="slots"
    )
    asignaciones: Mapped[list["TurnoGrillaVarianteAsignacionModel"]] = relationship(
        "TurnoGrillaVarianteAsignacionModel",
        back_populates="variante_slot",
        cascade="all, delete-orphan",
    )


class TurnoGrillaVarianteAsignacionModel(Base):
    __tablename__ = "turno_grilla_variante_asignacion"

    variante_slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("turno_grilla_variante_slot.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), primary_key=True
    )

    variante_slot: Mapped["TurnoGrillaVarianteSlotModel"] = relationship(
        "TurnoGrillaVarianteSlotModel", back_populates="asignaciones"
    )
