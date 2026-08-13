import uuid
from datetime import UTC, date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class VacacionesSolicitudModel(Base):
    """Solicitud de vacaciones. `charged_to_year` NULL = se imputa al año de
    `start_date` (paridad legacy). Fechas DATE sin hora (D11).
    """

    __tablename__ = "vacaciones_solicitud"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_vacaciones_solicitud_rango"),
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_vacaciones_solicitud_status",
        ),
        Index("ix_vacaciones_solicitud_rango", "start_date", "end_date"),
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
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_requested: Mapped[int] = mapped_column(Integer, nullable=False)
    charged_to_year: Mapped[int | None] = mapped_column(Integer, index=True)
    reason: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'PENDING'"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=lambda: datetime.now(UTC)
    )
