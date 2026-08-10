from sqlalchemy import BigInteger, PrimaryKeyConstraint, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class CustomerZoneContactModel(Base):
    """`zone=''` es la zona "default" real de un cliente — nunca usar NULL
    para representarla."""

    __tablename__ = "customer_zone_contacts"
    __table_args__ = (PrimaryKeyConstraint("customer_id", "zone"),)

    customer_id: Mapped[int] = mapped_column(BigInteger)
    zone: Mapped[str] = mapped_column(String, server_default=text("''"))
    sol_apellido: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    sol_nombre: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    sol_telefono: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    sol_email: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    sol_sector: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    dest_apellido: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    dest_nombre: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    dest_telefono: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    dest_email: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    dest_sector: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    observaciones: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
