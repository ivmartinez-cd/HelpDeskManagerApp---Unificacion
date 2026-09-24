"""Tabla `insumos_despacho_envio`: una fila por guía OCA que sigue Insumos > Despachados,
con el último estado leído de OCA (`oca_*`, NULL mientras OCA no la registre), la
clasificación del semáforo y el cierre manual de la alerta."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    false,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base

CHECK_COLOR_SEMAFORO = "color IN ('verde', 'amarillo', 'naranja', 'rojo', 'gris', 'cerrado')"
"""Misma expresión que la migración f2c7a9d4b1e8 (envío e historial de estados)."""


class DespachoEnvioModel(Base):
    __tablename__ = "insumos_despacho_envio"
    __table_args__ = (
        CheckConstraint(CHECK_COLOR_SEMAFORO, name="ck_insumos_despacho_envio_color"),
        Index("ix_insumos_despacho_envio_abierto", "abierto"),
        Index("ix_insumos_despacho_envio_color", "color"),
        Index("ix_insumos_despacho_envio_fecha_remito", "fecha_remito"),
    )

    guia: Mapped[str] = mapped_column(String(19), primary_key=True)
    id_distribucion: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_remito: Mapped[date] = mapped_column(Date, nullable=False)
    cliente: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    sucursal_cliente: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    oca_id_estado: Mapped[int | None] = mapped_column(Integer, nullable=True)
    oca_estado: Mapped[str | None] = mapped_column(String, nullable=True)
    oca_motivo: Mapped[str | None] = mapped_column(String, nullable=True)
    oca_sucursal: Mapped[str | None] = mapped_column(String, nullable=True)
    oca_fecha_estado: Mapped[date | None] = mapped_column(Date, nullable=True)
    oca_operativa: Mapped[str | None] = mapped_column(String, nullable=True)
    oca_orden_retiro: Mapped[str | None] = mapped_column(String, nullable=True)
    oca_cantidad_paquetes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    color: Mapped[str] = mapped_column(String(10), nullable=False)
    alerta: Mapped[bool] = mapped_column(Boolean, nullable=False)
    abierto: Mapped[bool] = mapped_column(Boolean, nullable=False)
    fecha_limite: Mapped[date | None] = mapped_column(Date, nullable=True)
    observacion: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    estado_desconocido: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=false()
    )
    consultado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ultimo_error: Mapped[str | None] = mapped_column(String, nullable=True)
    ultimo_error_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    alerta_cerrada_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    alerta_cerrada_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True
    )
    alerta_cerrada_por_nombre: Mapped[str | None] = mapped_column(String, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
