from datetime import UTC, datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class VacacionesConfigModel(Base):
    """Configuración singleton del módulo (SystemConfig legacy). Los campos
    `min_advance_notice_days`, `max_overlap_percent` y `max_overlap_count`
    existen por paridad con el legacy pero NINGUNA validación los usa (el
    legacy tampoco); no agregar lógica sobre ellos sin decisión explícita.
    """

    __tablename__ = "vacaciones_config"
    __table_args__ = (CheckConstraint("id = 'singleton'", name="ck_vacaciones_config_singleton"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, server_default=text("'singleton'"))
    seniority_tiers: Mapped[list[dict[str, float]]] = mapped_column(JSONB, nullable=False)
    next_year_open_month: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("10")
    )
    next_year_open_day: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    allow_advance_request: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    max_advance_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    allow_carry_over: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    max_carry_over_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    min_advance_notice_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("7")
    )
    max_overlap_percent: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("50")
    )
    max_overlap_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=lambda: datetime.now(UTC)
    )
