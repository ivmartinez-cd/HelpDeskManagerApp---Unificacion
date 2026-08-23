import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class SucursalCoordenadasModel(Base):
    """Coordenada resuelta por geocoding para una sucursal cliente sin pin
    usable en Siges — Siges es de solo lectura para este módulo. Solo hay
    fila para las efectivamente resueltas (ver domain/entities/
    sucursal_coordenadas.py); FK lógico por `siges_sucursal_id`, no hay tabla
    local de sucursales."""

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
