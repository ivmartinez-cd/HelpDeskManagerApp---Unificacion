from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class CotizacionDolarModel(Base):
    """Un registro por período (YYYY-MM) — dólar oficial. `fuente="dolarapi"` para
    el mes en curso (se pisa cada corrida del job hasta que cierra el mes);
    `fuente="argentinadatos"` para meses ya cerrados (valor definitivo, no se
    vuelve a tocar). Ver `SincronizarCotizacionesDolar`."""

    __tablename__ = "cotizaciones_dolar"

    periodo: Mapped[str] = mapped_column(String(7), primary_key=True)
    compra: Mapped[float] = mapped_column(Float, nullable=False)
    venta: Mapped[float] = mapped_column(Float, nullable=False)
    fecha_cotizacion: Mapped[date] = mapped_column(Date, nullable=False)
    fuente: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
