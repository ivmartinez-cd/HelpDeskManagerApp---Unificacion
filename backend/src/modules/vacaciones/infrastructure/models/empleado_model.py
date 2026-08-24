import uuid
from datetime import UTC, date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class VacacionesEmpleadoModel(Base):
    """Empleado del módulo de vacaciones. `user_id` vincula (opcionalmente) con
    la cuenta `app_user` de la plataforma — reemplaza al `User.employeeId`
    legacy invertido. `hire_date` es DATE (no timestamp): las fechas
    conceptuales del módulo no llevan hora (D11 del plan).
    """

    __tablename__ = "vacaciones_empleado"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')", name="ck_vacaciones_empleado_status"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    annual_vacation_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("22")
    )
    status: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'ACTIVE'"))
    color: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'#3b82f6'"))
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("department.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    cargo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vacaciones_cargo.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL"), unique=True
    )
    siges_empresa_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=lambda: datetime.now(UTC)
    )
