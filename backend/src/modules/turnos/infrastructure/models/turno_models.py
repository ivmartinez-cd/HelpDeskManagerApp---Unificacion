import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
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


class TurnoCasillaModel(Base):
    __tablename__ = "turno_casilla"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    slots: Mapped[list["TurnoSlotModel"]] = relationship(
        "TurnoSlotModel", back_populates="casilla", cascade="all, delete-orphan"
    )


class TurnoSlotModel(Base):
    __tablename__ = "turno_slot"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    casilla_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("turno_casilla.id", ondelete="CASCADE"), nullable=False
    )
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    dia_semana: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 0=Mon .. 6=Sun
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    casilla: Mapped["TurnoCasillaModel"] = relationship("TurnoCasillaModel", back_populates="slots")
    asignaciones: Mapped[list["TurnoAsignacionModel"]] = relationship(
        "TurnoAsignacionModel", back_populates="slot", cascade="all, delete-orphan"
    )


class TurnoAsignacionModel(Base):
    __tablename__ = "turno_asignacion"
    __table_args__ = (
        Index(
            "ux_turno_asignacion_slot_user_abierta",
            "slot_id",
            "user_id",
            unique=True,
            postgresql_where=text("vigente_hasta IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("turno_slot.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False
    )
    vigente_desde: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=text("CURRENT_DATE")
    )
    vigente_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)

    slot: Mapped["TurnoSlotModel"] = relationship("TurnoSlotModel", back_populates="asignaciones")


class TurnoAsignacionOverrideModel(Base):
    """Cobertura temporal de turnos (ver ADR-013) -- no reemplaza filas de
    `turno_asignacion`, se resuelve en lectura. `alcance_total=True` cubre
    todas las franjas del operador ausente; si es `False`, el alcance está
    en las filas de `turno_asignacion_override_slot`. `intercambio_id`
    (ADR-026) agrupa el par de overrides cruzados de un intercambio de
    turnos; NULL en una cobertura común."""

    __tablename__ = "turno_asignacion_override"
    __table_args__ = (CheckConstraint("desde <= hasta", name="ck_override_rango_valido"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    operador_ausente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False
    )
    operador_reemplazante_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False
    )
    desde: Mapped[date] = mapped_column(Date, nullable=False)
    hasta: Mapped[date] = mapped_column(Date, nullable=False)
    alcance_total: Mapped[bool] = mapped_column(Boolean, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVA")
    motivo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    intercambio_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    slots: Mapped[list["TurnoAsignacionOverrideSlotModel"]] = relationship(
        "TurnoAsignacionOverrideSlotModel",
        back_populates="override",
        cascade="all, delete-orphan",
    )


class TurnoAsignacionOverrideSlotModel(Base):
    """Alcance por franja puntual de una cobertura (solo tiene filas cuando
    `alcance_total=False` en la cobertura padre). FK a `turno_slot` con
    CASCADE: si se borra la franja, el alcance parcial que la referenciaba
    pierde sentido."""

    __tablename__ = "turno_asignacion_override_slot"

    override_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("turno_asignacion_override.id", ondelete="CASCADE"),
        primary_key=True,
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("turno_slot.id", ondelete="CASCADE"), primary_key=True
    )

    override: Mapped["TurnoAsignacionOverrideModel"] = relationship(
        "TurnoAsignacionOverrideModel", back_populates="slots"
    )
