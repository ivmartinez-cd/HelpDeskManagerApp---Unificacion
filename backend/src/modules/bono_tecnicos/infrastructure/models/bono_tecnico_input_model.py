from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class BonoTecnicoInputModel(Base):
    """Una fila por técnico y período — reescrita completa en cada guardado
    (ver SqlAlchemyBonoTecnicoInputRepository.upsert), como el snapshot de sla."""

    __tablename__ = "bono_tecnico_input"

    id_tecnico: Mapped[int] = mapped_column(Integer, primary_key=True)
    periodo: Mapped[int] = mapped_column(Integer, primary_key=True)
    tecnico: Mapped[str] = mapped_column(String(120), nullable=False)
    # Numeric(4,1), no Integer: admite medios días (ver BonoTecnicoInput).
    # asdecimal=False para que el driver devuelva float, no Decimal — el
    # resto del módulo (Puntaje, DTOs, schemas) ya trabaja en float.
    dias: Mapped[float] = mapped_column(Numeric(4, 1, asdecimal=False), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
