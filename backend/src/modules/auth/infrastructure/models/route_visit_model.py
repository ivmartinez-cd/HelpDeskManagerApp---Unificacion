import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class UserRouteVisit(Base):
    """Contador agregado por (usuario, día, ruta) — ADR-028. No es un event
    log: una fila por navegación no aporta nada al ranking y crece sin
    techo. La PK arranca en (user_id, visit_date) porque las dos queries que
    existen (top-N de una ventana, purga por antigüedad) filtran por ese
    prefijo; poner `route` antes de la fecha inutilizaría el índice para el
    rango de 30/90 días."""

    __tablename__ = "user_route_visit"
    __table_args__ = (
        CheckConstraint("visit_count > 0", name="ck_user_route_visit_count_positive"),
        CheckConstraint(
            "route ~ '^(/[a-z][a-z0-9]*(-[a-z0-9]+)*){1,4}$'",
            name="ck_user_route_visit_route_format",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), primary_key=True
    )
    visit_date: Mapped[date] = mapped_column(Date, primary_key=True)
    route: Mapped[str] = mapped_column(String(128), primary_key=True)
    visit_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
