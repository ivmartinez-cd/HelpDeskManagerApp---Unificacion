"""Tabla `insumos_despacho_accion`: lo que registra un operador desde "Registrar acción".
Solo se agregan filas. El usuario va con FK (ON DELETE SET NULL) y nombre denormalizado."""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    Text,
    false,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class DespachoAccionModel(Base):
    __tablename__ = "insumos_despacho_accion"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('llamado_cliente', 'mail_cliente', 'reclamo_oca', 'otro')",
            name="ck_insumos_despacho_accion_tipo",
        ),
        CheckConstraint(
            "resultado IN ('resuelto', 'pendiente', 'sin_respuesta')",
            name="ck_insumos_despacho_accion_resultado",
        ),
        Index("ix_insumos_despacho_accion_guia", "guia", "creada_en"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    guia: Mapped[str] = mapped_column(
        String(19),
        ForeignKey("insumos_despacho_envio.guia", ondelete="CASCADE"),
        nullable=False,
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    detalle: Mapped[str] = mapped_column(Text, nullable=False)
    resultado: Mapped[str] = mapped_column(String(20), nullable=False)
    cerro_alerta: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True
    )
    usuario_nombre: Mapped[str] = mapped_column(String, nullable=False)
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
