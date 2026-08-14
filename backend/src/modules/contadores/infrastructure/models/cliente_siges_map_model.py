from datetime import datetime

from sqlalchemy import DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class ClienteSigesMapModel(Base):
    """Alias manual `cliente` de Gestión → `ID_Empresa` de Siges — solo los
    nombres que el cruce automático de cliente_matcher no resuelve. Un mismo
    cliente puede tener varias filas: es la suma de esas empresas (ej.
    'Salta Refrescos' son 3 regiones en Siges)."""

    __tablename__ = "contadores_cliente_siges_map"

    cliente_gestion: Mapped[str] = mapped_column(String(200), primary_key=True)
    siges_empresa_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
