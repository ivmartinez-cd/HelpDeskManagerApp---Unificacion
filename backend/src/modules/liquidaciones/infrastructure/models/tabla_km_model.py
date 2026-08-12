import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class TablaKmModel(Base):
    """`spst_id` con `ondelete=SET NULL`: es una referencia opcional (nullable en el
    legacy) — borrar un SPST no debe arrastrar sus filas de Tabla KM."""

    __tablename__ = "tabla_kms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    prestador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prestadores.id", ondelete="CASCADE"), nullable=False
    )
    spst_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spsts.id", ondelete="SET NULL")
    )
    empresa_nombre: Mapped[str] = mapped_column(String, nullable=False)
    sucursal_nombre: Mapped[str] = mapped_column(String, nullable=False)
    observaciones: Mapped[str | None] = mapped_column(String)
    domicilio_cliente: Mapped[str | None] = mapped_column(String)
    localidad_cliente: Mapped[str | None] = mapped_column(String)
    provincia_cliente: Mapped[str | None] = mapped_column(String)
    kms_recorrido: Mapped[float] = mapped_column(Float, nullable=False)
    umbral_viatico: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("30.0")
    )
    aplica_viatico: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    kms_a_facturar: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0.0"))
    url_maps: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
