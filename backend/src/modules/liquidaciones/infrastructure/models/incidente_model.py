import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class IncidenteModel(Base):
    __tablename__ = "incidentes"
    __table_args__ = (Index("idx_incidentes_numero", "numero_incidente"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    liquidacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("liquidaciones.id", ondelete="CASCADE"), nullable=False
    )
    numero_incidente: Mapped[str] = mapped_column(String, nullable=False)
    rubro: Mapped[str | None] = mapped_column(String)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    empresa_nombre: Mapped[str | None] = mapped_column(String)
    sucursal_nombre: Mapped[str | None] = mapped_column(String)
    nro_serie: Mapped[str | None] = mapped_column(String)
    fecha_cierre: Mapped[date | None] = mapped_column(Date)

    costo_servicio_cobrado: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0.0")
    )
    cant_km_cobrado: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0.0")
    )
    costo_km_cobrado: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0.0")
    )
    total_viaje_cobrado: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0.0")
    )
    costo_total_cobrado: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0.0")
    )
    pasa_it: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    costo_servicio_esperado: Mapped[float | None] = mapped_column(Float)
    cant_km_esperado: Mapped[float | None] = mapped_column(Float)
    costo_km_esperado: Mapped[float | None] = mapped_column(Float)

    estado_validacion: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'pendiente'")
    )
