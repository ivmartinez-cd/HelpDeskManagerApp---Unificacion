"""Tabla `insumos_despacho_estado_historial`: cada cambio de estado que el job de
Despachados observa en OCA (no la historia completa de OCA)."""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.modules.insumos.infrastructure.models.despacho_envio_model import (
    CHECK_COLOR_SEMAFORO,
)
from src.shared.infrastructure.database.base import Base


class DespachoEstadoHistorialModel(Base):
    __tablename__ = "insumos_despacho_estado_historial"
    __table_args__ = (
        CheckConstraint(CHECK_COLOR_SEMAFORO, name="ck_insumos_despacho_estado_historial_color"),
        Index("ix_insumos_despacho_estado_historial_guia", "guia", "observado_en"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    guia: Mapped[str] = mapped_column(
        String(19),
        ForeignKey("insumos_despacho_envio.guia", ondelete="CASCADE"),
        nullable=False,
    )
    id_estado: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado: Mapped[str] = mapped_column(String, nullable=False)
    motivo: Mapped[str] = mapped_column(String, nullable=False)
    sucursal: Mapped[str] = mapped_column(String, nullable=False)
    fecha_estado: Mapped[date] = mapped_column(Date, nullable=False)
    color: Mapped[str] = mapped_column(String(10), nullable=False)
    observado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
