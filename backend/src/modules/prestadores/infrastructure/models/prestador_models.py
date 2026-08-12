import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.base import Base


class PrestadorModel(Base):
    __tablename__ = "prestador"
    __table_args__ = (UniqueConstraint("siges_empresa_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    siges_empresa_id: Mapped[int] = mapped_column(Integer, nullable=False)
    den_comercial: Mapped[str] = mapped_column(String(200), nullable=False)
    razon_social: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cuit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    operador_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )

    contactos: Mapped[list["PrestadorContactoModel"]] = relationship(
        "PrestadorContactoModel", back_populates="prestador", cascade="all, delete-orphan"
    )
    historial: Mapped[list["PrestadorAsignacionHistorialModel"]] = relationship(
        "PrestadorAsignacionHistorialModel",
        back_populates="prestador",
        cascade="all, delete-orphan",
    )


class PrestadorContactoModel(Base):
    __tablename__ = "prestador_contacto"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    prestador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prestador.id", ondelete="CASCADE"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_principal: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    prestador: Mapped["PrestadorModel"] = relationship(
        "PrestadorModel", back_populates="contactos"
    )


class PrestadorAsignacionHistorialModel(Base):
    __tablename__ = "prestador_asignacion_historial"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    prestador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prestador.id", ondelete="CASCADE"), nullable=False
    )
    operador_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True
    )
    desde: Mapped[date] = mapped_column(Date, nullable=False)
    hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    prestador: Mapped["PrestadorModel"] = relationship(
        "PrestadorModel", back_populates="historial"
    )
