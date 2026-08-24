import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class SolicitudTvModel(Base):
    """Una fila por solicitud de TV — reemplaza el Sheet legacy. `periodo`
    desnormaliza `fecha` (AAAAMM) para poder filtrar/agrupar en SQL sin
    calcularlo en Python en cada consulta."""

    __tablename__ = "bono_tecnico_solicitud_tv"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('PENDIENTE', 'APROBADA', 'RECHAZADA')",
            name="ck_bono_tecnico_solicitud_tv_estado",
        ),
        Index("ix_bono_tecnico_solicitud_tv_periodo_tecnico", "periodo", "id_tecnico"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    id_tecnico: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    tecnico: Mapped[str] = mapped_column(String(120), nullable=False)
    periodo: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    razon_social: Mapped[str] = mapped_column(String(200), nullable=False)
    sucursal: Mapped[str] = mapped_column(String(200), nullable=False)
    tarea_realizada: Mapped[str] = mapped_column(String(2000), nullable=False)
    estado: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'PENDIENTE'"), index=True
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    resuelta_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resuelta_por_email: Mapped[str | None] = mapped_column(String(255))
    motivo_rechazo: Mapped[str | None] = mapped_column(String(500))
