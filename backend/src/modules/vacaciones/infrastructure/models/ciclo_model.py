import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class VacacionesCicloModel(Base):
    """Ciclo anual de vacaciones por empleado. `carry_over` se persiste con
    write-behind al calcular saldos (paridad con el legacy); `is_open` se
    materializa lazy cuando la política de apertura lo habilita (D7).
    """

    __tablename__ = "vacaciones_ciclo"
    __table_args__ = (
        UniqueConstraint("empleado_id", "year", name="uq_vacaciones_ciclo_empleado_year"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    empleado_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vacaciones_empleado.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    annual_days: Mapped[int] = mapped_column(Integer, nullable=False)
    carry_over: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=lambda: datetime.now(UTC)
    )
