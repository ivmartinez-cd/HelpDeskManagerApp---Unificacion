"""Modelos de geolocalización: resoluciones de coordenadas por sucursal Siges
sin pin, y previews del cálculo masivo de distancias. El cache de geocodes
(antes `GeocodeCacheModel` acá) se movió a
`shared/infrastructure/geocoding/geocode_cache_model.py` — es genérico,
también lo usa preventivos."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class SucursalCoordenadasModel(Base):
    """Coordenadas elegidas (geocode confirmado o manual) para sucursales
    cliente SIN pin en Siges — Siges es de solo lectura para este módulo."""

    __tablename__ = "sucursal_coordenadas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    prestador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prestadores.id", ondelete="CASCADE"), nullable=False
    )
    siges_sucursal_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    empresa_nombre: Mapped[str] = mapped_column(String, nullable=False)
    sucursal_nombre: Mapped[str] = mapped_column(String, nullable=False)
    direccion_normalizada: Mapped[str | None] = mapped_column(String)
    latitud: Mapped[float | None] = mapped_column(Float)
    longitud: Mapped[float | None] = mapped_column(Float)
    procedencia: Mapped[str | None] = mapped_column(String)
    formatted_address: Mapped[str | None] = mapped_column(String)
    fecha_resolucion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )


class CalculoKmPreviewModel(Base):
    """Propuesta del cálculo masivo (two-step): el apply materializa este
    payload sin volver a llamar a Google."""

    __tablename__ = "calculo_km_previews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    prestador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prestadores.id", ondelete="CASCADE"), nullable=False
    )
    filas: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    sin_ubicar: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    sin_ruta: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    elementos_google: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    sin_actividad: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
