from datetime import datetime

from sqlalchemy import DateTime, Integer, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class PendientesSnapshotModel(Base):
    """Fila única — reescrita completa en cada refresh. `version=1` es la clave
    sintética constante: solo existe un snapshot global de pendientes (sin
    dimensión de período, a diferencia del snapshot de SLA)."""

    __tablename__ = "sla_pendientes_snapshot"

    version: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    incidentes: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
    por_prestador: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
