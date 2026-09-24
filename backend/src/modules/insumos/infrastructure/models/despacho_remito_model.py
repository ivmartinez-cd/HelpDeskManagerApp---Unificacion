"""Tablas `insumos_despacho_remito` e `insumos_despacho_incidente`: de qué remitos de Siges
sale cada guía y qué pedidos de insumos viajan en cada remito. `id_remito` es el
`Remito_Cab.Id_Remito` de Siges (clave natural, no autonumérica)."""

from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class DespachoRemitoModel(Base):
    __tablename__ = "insumos_despacho_remito"
    __table_args__ = (
        Index("ix_insumos_despacho_remito_guia", "guia"),
        Index("ix_insumos_despacho_remito_numero", "numero_remito"),
    )

    id_remito: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    guia: Mapped[str] = mapped_column(
        String(19),
        ForeignKey("insumos_despacho_envio.guia", ondelete="CASCADE"),
        nullable=False,
    )
    numero_remito: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fecha_remito: Mapped[date] = mapped_column(Date, nullable=False)
    bultos: Mapped[int] = mapped_column(Integer, nullable=False)
    id_distribucion: Mapped[int] = mapped_column(Integer, nullable=False)
    cliente: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    sucursal_cliente: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    entrega_a: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )


class DespachoIncidenteModel(Base):
    __tablename__ = "insumos_despacho_incidente"
    __table_args__ = (Index("ix_insumos_despacho_incidente_numero", "numero"),)

    id_remito: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("insumos_despacho_remito.id_remito", ondelete="CASCADE"),
        primary_key=True,
    )
    numero: Mapped[str] = mapped_column(String(13), primary_key=True)
    numero_cliente: Mapped[str] = mapped_column(String, nullable=False, server_default="")
