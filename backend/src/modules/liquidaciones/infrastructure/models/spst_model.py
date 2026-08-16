import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class SpstModel(Base):
    """Sin `ondelete` en `prestador_id`: la baja de un prestador con SPSTs vinculados se
    maneja explícitamente en el caso de uso (mismo comportamiento que el legacy, que
    borraba en cascada solo a través del ORM, nunca a nivel DB — acá se refuerza con
    `ondelete=CASCADE` porque es intencional y equivalente en efecto neto)."""

    __tablename__ = "spsts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    prestador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prestadores.id", ondelete="CASCADE"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    domicilio: Mapped[str | None] = mapped_column(String)
    localidad: Mapped[str | None] = mapped_column(String)
    provincia: Mapped[str | None] = mapped_column(String)
    zona: Mapped[str | None] = mapped_column(String)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    siges_empresa_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    siges_base_sucursal_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
