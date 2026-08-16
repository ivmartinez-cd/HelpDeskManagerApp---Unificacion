import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class LiquidacionPrestadorModel(Base):
    __tablename__ = "prestadores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    nombre_corto: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    cuit: Mapped[str | None] = mapped_column(String)
    region: Mapped[str | None] = mapped_column(String)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    siges_empresa_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    cd_prestador_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    siges_base_sucursal_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
