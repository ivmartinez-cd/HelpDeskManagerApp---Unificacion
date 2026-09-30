from datetime import datetime

from sqlalchemy import DateTime, Integer, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class AvisoVisitaSucursalModel(Base):
    """Un par (caso de Mesa de Ayuda, visita de técnico en su sucursal) ya
    avisado por mail — evita repetir el aviso en cada ciclo del job."""

    __tablename__ = "sla_avisos_visita_sucursal"

    id_incidente_mda: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_incidente_visita: Mapped[int] = mapped_column(Integer, primary_key=True)
    enviado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
