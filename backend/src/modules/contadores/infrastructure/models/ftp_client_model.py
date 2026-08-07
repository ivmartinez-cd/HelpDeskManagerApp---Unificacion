import uuid

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.modules.contadores.domain.entities.ftp_client import DEFAULT_PATH, DEFAULT_PATTERN
from src.shared.infrastructure.database.base import Base


class FtpClientModel(Base):
    __tablename__ = "ftp_clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    host: Mapped[str] = mapped_column(String, nullable=False)
    user: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text(f"'{DEFAULT_PATH}'")
    )
    pattern: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text(f"'{DEFAULT_PATTERN}'")
    )
