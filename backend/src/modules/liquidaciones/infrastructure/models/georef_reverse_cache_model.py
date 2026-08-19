import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class GeorefReverseCacheModel(Base):
    """Cache de reverse geocoding de Georef por pin redondeado a 4 decimales
    (~11 m) — evita re-consultar el mismo punto. `provincia_nombre is None`
    con fila existente significa "consultado, sin cobertura Georef ahí"."""

    __tablename__ = "georef_reverse_cache"
    __table_args__ = (UniqueConstraint("lat_redondeada", "lon_redondeada"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    lat_redondeada: Mapped[float] = mapped_column(Float, nullable=False)
    lon_redondeada: Mapped[float] = mapped_column(Float, nullable=False)
    provincia_nombre: Mapped[str | None] = mapped_column(String)
    provincia_id: Mapped[str | None] = mapped_column(String)
    departamento_nombre: Mapped[str | None] = mapped_column(String)
    departamento_id: Mapped[str | None] = mapped_column(String)
    fecha_consulta: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
