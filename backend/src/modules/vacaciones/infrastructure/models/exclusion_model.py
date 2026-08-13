import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class VacacionesExclusionModel(Base):
    """Par de empleados que no pueden solapar vacaciones. El CHECK a < b
    normaliza en el schema el orden que el legacy normalizaba en código, y hace
    al UNIQUE insensible al orden de carga.
    """

    __tablename__ = "vacaciones_exclusion"
    __table_args__ = (
        UniqueConstraint("empleado_a_id", "empleado_b_id", name="uq_vacaciones_exclusion_par"),
        CheckConstraint("empleado_a_id < empleado_b_id", name="ck_vacaciones_exclusion_orden"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    empleado_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vacaciones_empleado.id", ondelete="CASCADE"),
        nullable=False,
    )
    empleado_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vacaciones_empleado.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
