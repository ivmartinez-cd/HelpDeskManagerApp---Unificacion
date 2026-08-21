import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.modules.contadores.domain.entities.cliente_nuevo import (
    ESTADO_ESPERANDO_INSTALACION,
    ESTADOS_CLIENTE_NUEVO,
    MAX_CLIENTE,
    MAX_NOTAS,
)
from src.shared.infrastructure.database.base import Base

_ESTADOS_SQL = ", ".join(f"'{e}'" for e in ESTADOS_CLIENTE_NUEVO)


class ClienteNuevoModel(Base):
    __tablename__ = "contadores_cliente_nuevo"
    __table_args__ = (
        CheckConstraint(f"estado IN ({_ESTADOS_SQL})", name="ck_cliente_nuevo_estado"),
        CheckConstraint(
            "dia_corte IS NULL OR (dia_corte BETWEEN 1 AND 31)", name="ck_cliente_nuevo_dia_corte"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cliente: Mapped[str] = mapped_column(String(MAX_CLIENTE), nullable=False)
    siges_empresa_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contrato_nro: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fecha_firma: Mapped[date | None] = mapped_column(Date, nullable=True)
    vendedor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    operador_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    implementacion_servicio: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fecha_estimada_implementacion: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_estimada_primera_facturacion: Mapped[date | None] = mapped_column(Date, nullable=True)
    dia_corte: Mapped[int | None] = mapped_column(Integer, nullable=True)
    equipos_previstos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=ESTADO_ESPERANDO_INSTALACION
    )
    stc_enviado_el: Mapped[date | None] = mapped_column(Date, nullable=True)
    notas: Mapped[str | None] = mapped_column(String(MAX_NOTAS), nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
