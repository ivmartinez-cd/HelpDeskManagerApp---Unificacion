import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class EstimLogModel(Base):
    """Auditoría de estimaciones del Estimador de Contadores (MODELO_DE_DATOS.md
    §5, REGLAS_DE_NEGOCIO.md §11) — append-only, nunca se pisa un registro
    (sin UPDATE/DELETE desde la app). Reemplaza la deuda reconocida del
    sistema original (SQLite fragmentado por operador, sin consolidar).
    `operador_email` es un snapshot (no solo la FK) para que el log siga
    siendo legible aunque el usuario se borre o cambie de email."""

    __tablename__ = "contadores_estim_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    operador_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True
    )
    operador_email: Mapped[str] = mapped_column(String(255), nullable=False)
    nro_proceso: Mapped[int | None] = mapped_column(Integer, nullable=True)
    id_maquina: Mapped[int] = mapped_column(Integer, nullable=False)
    clase: Mapped[str] = mapped_column(String(10), nullable=False)
    accion: Mapped[str] = mapped_column(String(30), nullable=False)
    # Nullable: los endpoints simples (marcar-pendiente/nota/aceptar) no
    # siempre tienen a mano la fecha objetivo del proceso.
    fecha_objetivo: Mapped[date | None] = mapped_column(Date, nullable=True)
    contador_anterior: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    contador_propuesto: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    tipo_toma_grabado: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fuente: Mapped[str | None] = mapped_column(String(40), nullable=True)
    metodo_detalle: Mapped[str | None] = mapped_column(String(200), nullable=True)
    observacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Composición estructurada cuando aplica (P/L elegidos a mano, parque
    # usado, días/tasa de la regla de tres) — variable según `accion`, no
    # vale la pena una columna fija por cada posible campo.
    detalle: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
