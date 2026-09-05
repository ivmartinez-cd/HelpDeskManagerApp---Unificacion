from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class DecisionOperadorModel(Base):
    """Estado vigente (pendiente/nota) de la decisión del operador sobre un
    (equipo, clase) de un proceso REAL — una fila por equipo+clase, se pisa
    en cada acción. Complementa, no reemplaza, `contadores_estim_log`
    (append-only): esta tabla es solo el último estado, para no reconstruirlo
    del historial completo en cada carga del tablero. El modo ejemplo sigue
    usando `DecisionesOperadorStore` (en memoria)."""

    __tablename__ = "contadores_decision_operador"

    id_maquina: Mapped[int] = mapped_column(Integer, primary_key=True)
    clase: Mapped[str] = mapped_column(String(10), primary_key=True)
    pendiente: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    nota: Mapped[str | None] = mapped_column(Text, nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
