import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class VacacionesCargoModel(Base):
    """Cargo/posición. `max_simultaneos` absorbe el PositionOverlapLimit legacy
    (tabla 1:1); NULL = sin límite de vacaciones simultáneas para el cargo.
    """

    __tablename__ = "vacaciones_cargo"
    __table_args__ = (
        CheckConstraint(
            "max_simultaneos IS NULL OR max_simultaneos >= 1",
            name="ck_vacaciones_cargo_max_simultaneos",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    max_simultaneos: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=lambda: datetime.now(UTC)
    )
