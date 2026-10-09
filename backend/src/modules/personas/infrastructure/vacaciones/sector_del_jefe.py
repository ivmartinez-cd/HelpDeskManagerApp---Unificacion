"""Sector que un usuario tiene asignado como jefe en Gestión de Personal
(`user_module_scope` de vacaciones) — dependencia cross-module solo en
infrastructure (ADR-040)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_sector_manager_repository import (  # noqa: E501
    SqlAlchemySectorManagerRepository,
)


async def sector_del_jefe(db: AsyncSession, user_id: uuid.UUID) -> uuid.UUID | None:
    return await SqlAlchemySectorManagerRepository(db).get_sector_de_usuario(user_id)
