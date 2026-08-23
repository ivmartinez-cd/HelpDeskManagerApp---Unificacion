import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class SucursalCoordenadasModel(Base):
    """Coordenada resuelta para una sucursal cliente sin pin usable en Siges
    — Siges es de solo lectura para este módulo. Solo hay fila para las
    efectivamente resueltas (ver domain/entities/sucursal_coordenadas.py); FK
    lógico por `siges_sucursal_id`, no hay tabla local de sucursales.
    `corregido_por_*`/`nota` quedan NULL cuando la fila viene de geocoding
    automático; se completan en una corrección manual desde la UI
    (2026-08-23)."""

    __tablename__ = "preventivos_sucursal_coordenadas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    siges_sucursal_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    latitud: Mapped[float] = mapped_column(Float, nullable=False)
    longitud: Mapped[float] = mapped_column(Float, nullable=False)
    formatted_address: Mapped[str] = mapped_column(String, nullable=False)
    fecha_resolucion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    corregido_por_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=True
    )
    corregido_por_nombre: Mapped[str | None] = mapped_column(String(120), nullable=True)
    nota: Mapped[str | None] = mapped_column(String(300), nullable=True)
