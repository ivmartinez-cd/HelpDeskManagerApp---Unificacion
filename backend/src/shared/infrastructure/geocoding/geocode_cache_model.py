"""Modelo ORM del cache de geocodes — tabla `geocode_cache`, creada
originalmente por la migración de liquidaciones (b2f7d914ce08); el traslado
de este modelo a `shared` es solo de código Python, la tabla no cambia."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class GeocodeCacheModel(Base):
    """Cache por dirección normalizada — una dirección ya consultada (aunque
    haya dado ZERO_RESULTS) no se vuelve a pedir a Google."""

    __tablename__ = "geocode_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    direccion_normalizada: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    candidatos: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    fecha_consulta: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
