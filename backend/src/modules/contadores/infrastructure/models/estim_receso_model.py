from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class EstimRecesoModel(Base):
    """Calendario de recesos de clientes de un proceso REAL (REGLAS_DE_NEGOCIO
    §6, MODELO_DE_DATOS.md §5) — CRUD completo desde la app. El modo ejemplo
    sigue usando `RecesosEjemploStore` (en memoria): mezclar sus IDs de
    grupo económico/anexo ficticios con IDs reales de Siges en esta misma
    tabla sería un riesgo de colisión real, no solo teórico."""

    __tablename__ = "contadores_estim_receso"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_grupo_economico: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    id_anexo: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fecha_desde: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_hasta: Mapped[date] = mapped_column(Date, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(200), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
