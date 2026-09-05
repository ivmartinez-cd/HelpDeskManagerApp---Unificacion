from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class DecisionOperadorModel(Base):
    """Estado vigente (pendiente/nota/valor manual aceptado) de la decisión
    del operador sobre un (equipo, clase) de un proceso REAL — una fila por
    equipo+clase, se pisa en cada acción. Complementa, no reemplaza,
    `contadores_estim_log` (append-only): esta tabla es solo el último
    estado, para no reconstruirlo del historial completo en cada carga del
    tablero ni del export. El modo ejemplo sigue usando
    `DecisionesOperadorStore` (en memoria).

    `manual_*` solo tienen valor cuando el operador aceptó explícitamente un
    P/L manual o un método forzado (distinto del cálculo automático del
    motor) — si son NULL, el tablero y el export usan el cálculo automático."""

    __tablename__ = "contadores_decision_operador"

    id_maquina: Mapped[int] = mapped_column(Integer, primary_key=True)
    clase: Mapped[str] = mapped_column(String(10), primary_key=True)
    pendiente: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    nota: Mapped[str | None] = mapped_column(Text, nullable=True)
    manual_contador_propuesto: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    manual_tipo_toma: Mapped[int | None] = mapped_column(Integer, nullable=True)
    manual_fuente: Mapped[str | None] = mapped_column(String(40), nullable=True)
    manual_metodo_detalle: Mapped[str | None] = mapped_column(String(200), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
