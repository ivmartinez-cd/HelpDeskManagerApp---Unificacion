from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class SlaPeriodoSnapshotModel(Base):
    """Un registro por período (AAAAMM) — reescrito completo en cada refresh,
    nunca versionado ni acumulado (ver SqlAlchemySlaSnapshotRepository.upsert)."""

    __tablename__ = "sla_periodo_snapshot"

    periodo: Mapped[int] = mapped_column(Integer, primary_key=True)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    correctos: Mapped[int] = mapped_column(Integer, nullable=False)
    vencidos: Mapped[int] = mapped_column(Integer, nullable=False)
    pct_correctos: Mapped[float] = mapped_column(Float, nullable=False)
    pct_vencidos: Mapped[float] = mapped_column(Float, nullable=False)
    vencidos_por_tecnico: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
    incidentes_vencidos: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
