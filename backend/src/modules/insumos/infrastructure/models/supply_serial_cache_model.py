from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class SupplySerialCacheModel(Base):
    """Cache de supplies vistos en Canal Directo (por ID exacto, vía scan
    incremental) — única fuente que ve pedidos con origen Interno, que
    `getTopSupplies`/el portal excluyen. `fecha` era `DD/MM/YYYY` de CD en
    el legacy; acá va directo como TIMESTAMPTZ (parseada al escribir, no en
    cada lectura). El índice funcional `lower(serial)` (reemplaza el
    `COLLATE NOCASE` duplicado del legacy) se declara en la migración, no
    acá — SQLAlchemy declarative no expresa bien índices funcionales."""

    __tablename__ = "supply_serial_cache"

    supply_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    serial: Mapped[str] = mapped_column(String, nullable=False, index=True)
    estado: Mapped[str | None] = mapped_column(String)
    empresa_id: Mapped[str | None] = mapped_column(String)
    fecha: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sku: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    cached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
