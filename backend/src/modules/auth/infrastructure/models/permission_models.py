import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base

_KEY_FORMAT = r"^[a-z][a-z0-9-]{1,39}$"


class Module(Base):
    """Catálogo de módulos — seeded por migración, no editable desde la UI."""

    __tablename__ = "module"
    __table_args__ = (CheckConstraint(f"key ~ '{_KEY_FORMAT}'", name="ck_module_key_format"),)

    key: Mapped[str] = mapped_column(String, primary_key=True)
    label: Mapped[str] = mapped_column(String, nullable=False)
    route: Mapped[str] = mapped_column(String, nullable=False)
    icon: Mapped[str] = mapped_column(String, nullable=False)
    sort_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("100")
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class Action(Base):
    """Catálogo de acciones — seeded por migración, no editable desde la UI."""

    __tablename__ = "action"
    __table_args__ = (CheckConstraint(f"key ~ '{_KEY_FORMAT}'", name="ck_action_key_format"),)

    key: Mapped[str] = mapped_column(String, primary_key=True)
    label: Mapped[str] = mapped_column(String, nullable=False)


class ModuleAction(Base):
    """Declara qué acciones tienen sentido en qué módulo."""

    __tablename__ = "module_action"

    module_key: Mapped[str] = mapped_column(
        ForeignKey("module.key", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True
    )
    action_key: Mapped[str] = mapped_column(
        ForeignKey("action.key", onupdate="CASCADE", ondelete="RESTRICT"), primary_key=True
    )


class PermissionGrant(Base):
    """LA MATRIZ. 1 fila = 1 permiso concedido. Ausencia de fila = denegado."""

    __tablename__ = "permission_grant"
    __table_args__ = (
        ForeignKeyConstraint(
            ["module_key", "action_key"],
            ["module_action.module_key", "module_action.action_key"],
            onupdate="CASCADE",
            ondelete="CASCADE",
            name="fk_permission_grant_module_action",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), primary_key=True
    )
    module_key: Mapped[str] = mapped_column(String, primary_key=True)
    action_key: Mapped[str] = mapped_column(String, primary_key=True)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL")
    )


class UserModuleScope(Base):
    """Alcance sectorial PREVISTO, SIN LÓGICA en esta fase (ver ADR de auth)."""

    __tablename__ = "user_module_scope"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), primary_key=True
    )
    module_key: Mapped[str] = mapped_column(
        ForeignKey("module.key", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True
    )
    scope_department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("department.id", ondelete="RESTRICT")
    )


class PermissionAudit(Base):
    __tablename__ = "permission_audit"
    __table_args__ = (
        CheckConstraint("operation IN ('grant', 'revoke')", name="ck_permission_audit_operation"),
        Index("ix_permission_audit_target", "target_user_id", text("occurred_at DESC")),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL")
    )
    target_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False
    )
    module_key: Mapped[str] = mapped_column(String, nullable=False)
    action_key: Mapped[str] = mapped_column(String, nullable=False)
    operation: Mapped[str] = mapped_column(String, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
