import uuid
from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base

_TIPOS = (
    "'DESCUENTO_DIA', 'BAJA_ENFERMEDAD', 'TRAMITE_PERSONAL', 'GUARDIA', "
    "'DIA_ESTUDIO', 'HOME_OFFICE', 'OTHER'"
)


class VacacionesAusenciaModel(Base):
    """Baja/ausencia (Absence legacy). Nace APPROVED; `half_day` computa 0.5
    en reportes sin alterar `days_count`. Fechas DATE sin hora (D11).
    """

    __tablename__ = "vacaciones_ausencia"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_vacaciones_ausencia_rango"),
        CheckConstraint(
            f"tipo IN ({_TIPOS})",
            name="ck_vacaciones_ausencia_tipo",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_vacaciones_ausencia_status",
        ),
        Index("ix_vacaciones_ausencia_rango", "start_date", "end_date"),
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
    days_count: Mapped[int] = mapped_column(Integer, nullable=False)
    half_day: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    tipo: Mapped[str] = mapped_column(String, nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'APPROVED'"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=lambda: datetime.now(UTC)
    )
