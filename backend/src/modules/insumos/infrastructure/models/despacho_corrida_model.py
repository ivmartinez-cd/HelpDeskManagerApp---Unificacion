"""Tabla `insumos_despacho_corrida`: cada ejecución del job de Despachados (programada o
"Actualizar ahora"). `terminada_en` es NULL mientras la corrida está en curso."""

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Identity, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class DespachoCorridaModel(Base):
    __tablename__ = "insumos_despacho_corrida"
    __table_args__ = (
        CheckConstraint(
            "origen IN ('programada', 'manual')", name="ck_insumos_despacho_corrida_origen"
        ),
        Index("ix_insumos_despacho_corrida_iniciada_en", "iniciada_en"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    origen: Mapped[str] = mapped_column(String(12), nullable=False)
    iniciada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    terminada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    usuario_nombre: Mapped[str | None] = mapped_column(String, nullable=True)
    envios_nuevos: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    consultas_ok: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    consultas_error: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error: Mapped[str | None] = mapped_column(String, nullable=True)
