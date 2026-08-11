from datetime import UTC, datetime

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class OperadorModel(Base):
    """Catálogo local de operadores de facturación de Gestión (scrapeado de
    /planificacion/ver) — ver GestionPlanificacionClient.get_operadores."""

    __tablename__ = "contadores_operadores"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    color: Mapped[str | None] = mapped_column(String)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=lambda: datetime.now(UTC),
    )
