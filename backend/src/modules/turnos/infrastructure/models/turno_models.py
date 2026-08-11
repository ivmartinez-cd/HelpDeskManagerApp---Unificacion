import uuid
from datetime import date, time

from sqlalchemy import Boolean, Date, ForeignKey, Integer, SmallInteger, String, Time, text
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
