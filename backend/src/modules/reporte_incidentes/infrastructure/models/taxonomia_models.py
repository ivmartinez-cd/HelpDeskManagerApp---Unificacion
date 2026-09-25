from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.base import Base


class ReporteIncidentesCategoriaModel(Base):
    """Categoría de la taxonomía de tipificación (antes `categories.json`)."""

    __tablename__ = "reporte_incidentes_categoria"
    __table_args__ = (
        # Nombre único sin distinguir mayúsculas (regla del ABM del legacy).
        Index("uq_reporte_incidentes_categoria_nombre", func.lower(text("nombre")), unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    color: Mapped[str] = mapped_column(String(9), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    orden: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    subcategorias: Mapped[list["ReporteIncidentesSubcategoriaModel"]] = relationship(
        order_by="ReporteIncidentesSubcategoriaModel.orden",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ReporteIncidentesSubcategoriaModel(Base):
    __tablename__ = "reporte_incidentes_subcategoria"
    __table_args__ = (
        UniqueConstraint("categoria_id", "nombre", name="uq_reporte_incidentes_subcategoria"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("reporte_incidentes_categoria.id", ondelete="CASCADE"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    orden: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class ReporteIncidentesTipificacionModel(Base):
    """Caché de tipificaciones (antes `classification-cache.json`).

    Una fila por caso distinto (`descripcion|causa|solucion`), indexada por el
    sha256 de esa clave. Guarda la respuesta cruda con su confianza: el umbral
    ("solo alta") se aplica al leer. `origen`: ia | manual | legacy."""

    __tablename__ = "reporte_incidentes_tipificacion"

    clave_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    clave: Mapped[str] = mapped_column(Text, nullable=False)
    categoria: Mapped[str] = mapped_column(String(120), nullable=False)
    subcategoria: Mapped[str] = mapped_column(String(160), nullable=False)
    confianza: Mapped[str] = mapped_column(String(10), nullable=False)
    origen: Mapped[str] = mapped_column(String(10), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
