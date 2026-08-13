"""Auditoría: escritura bound al usuario actuante + lectura paginada.

El registrador NUNCA lanza (contrato del puerto: la auditoría no rompe el
flujo principal, paridad recordAudit legacy); el error se loguea acá con
contexto, en el punto donde se atrapa (§6 de la guía).
"""

import logging
import uuid
from datetime import timedelta

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.vacaciones.domain.entities.registro_auditoria import RegistroAuditoria
from src.modules.vacaciones.domain.repositories.auditoria import FiltrosAuditoria
from src.modules.vacaciones.infrastructure.models.audit_log_model import (
    VacacionesAuditLogModel,
)

_logger = logging.getLogger(__name__)


class SqlAlchemyRegistradorAuditoria:
    def __init__(self, session: AsyncSession, user_id: uuid.UUID | None) -> None:
        self._session = session
        self._user_id = user_id

    async def registrar(
        self,
        accion: str,
        entidad: str,
        entidad_id: str | None,
        metadata: dict[str, object],
    ) -> None:
        try:
            self._session.add(
                VacacionesAuditLogModel(
                    accion=accion,
                    entidad=entidad,
                    entidad_id=entidad_id,
                    user_id=self._user_id,
                    metadata_json=metadata or None,
                )
            )
            await self._session.flush()
        except Exception as exc:  # la auditoría no puede romper el flujo principal
            _logger.error(
                "No se pudo registrar la entrada de auditoría",
                extra={"accion": accion, "entidad": entidad, "entidad_id": entidad_id},
                exc_info=exc,
            )


def _to_entity(row: VacacionesAuditLogModel) -> RegistroAuditoria:
    return RegistroAuditoria(
        id=row.id,
        accion=row.accion,
        entidad=row.entidad,
        entidad_id=row.entidad_id,
        user_id=row.user_id,
        created_at=row.created_at,
        metadata=dict(row.metadata_json or {}),
    )


def _aplicar_filtros(
    stmt: Select[tuple[VacacionesAuditLogModel]], filtros: FiltrosAuditoria
) -> Select[tuple[VacacionesAuditLogModel]]:
    if filtros.entidad is not None:
        stmt = stmt.where(VacacionesAuditLogModel.entidad == filtros.entidad)
    if filtros.accion is not None:
        stmt = stmt.where(VacacionesAuditLogModel.accion == filtros.accion)
    if filtros.desde is not None:
        stmt = stmt.where(
            VacacionesAuditLogModel.created_at >= filtros.desde
        )
    if filtros.hasta is not None:
        # `hasta` es inclusivo a nivel día (la columna es timestamptz).
        limite = filtros.hasta + timedelta(days=1)
        stmt = stmt.where(
            VacacionesAuditLogModel.created_at < limite
        )
    if filtros.search:
        patron = f"%{filtros.search}%"
        emails = (
            select(AppUser.id).where(AppUser.email.ilike(patron)).scalar_subquery()
        )
        stmt = stmt.where(
            or_(
                VacacionesAuditLogModel.accion.ilike(patron),
                VacacionesAuditLogModel.entidad.ilike(patron),
                VacacionesAuditLogModel.user_id.in_(emails),
            )
        )
    return stmt


class SqlAlchemyAuditoriaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_pagina(
        self, filtros: FiltrosAuditoria, *, offset: int, limit: int
    ) -> tuple[list[RegistroAuditoria], int]:
        base = _aplicar_filtros(select(VacacionesAuditLogModel), filtros)
        total = (
            await self._session.execute(
                select(func.count()).select_from(base.subquery())
            )
        ).scalar_one()
        rows = (
            (
                await self._session.execute(
                    base.order_by(VacacionesAuditLogModel.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return [_to_entity(r) for r in rows], total
