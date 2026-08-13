import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class VacacionesFeriadoModel(Base):
    """Feriado. `deducts_vacation=false` (default legacy) significa que si cae
    exactamente en el inicio de una solicitud desplaza el conteo en 1 día; los
    feriados en el medio del rango cuentan igual (LCT, días corridos).
    """

    __tablename__ = "vacaciones_feriado"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    deducts_vacation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=lambda: datetime.now(UTC)
    )
