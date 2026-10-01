"""Auditoría: escritura bound al usuario actuante + lectura paginada.

El registrador NUNCA lanza (contrato del puerto: la auditoría no rompe el
flujo principal, paridad recordAudit legacy); el error se loguea acá con
contexto, en el punto donde se atrapa (§6 de la guía).
"""

import logging
import uuid
from datetime import timedelta
from typing import Any

from sqlalchemy import ColumnElement, Select, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.vacaciones.domain.entities.registro_auditoria import RegistroAuditoria
from src.modules.vacaciones.domain.repositories.auditoria import (
    ORDEN_POR_DEFECTO,
    FiltrosAuditoria,
    OrdenAuditoria,
)
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
        stmt = stmt.where(VacacionesAuditLogModel.created_at >= filtros.desde)
    if filtros.hasta is not None:
        # `hasta` es inclusivo a nivel día (la columna es timestamptz).
        limite = filtros.hasta + timedelta(days=1)
        stmt = stmt.where(VacacionesAuditLogModel.created_at < limite)
    if filtros.search:
        stmt = stmt.where(_condicion_busqueda(filtros.search))
    return stmt


def _condicion_busqueda(search: str) -> ColumnElement[bool]:
    """Texto libre sobre acción, entidad o email del usuario actuante."""
    patron = f"%{search}%"
    emails = select(AppUser.id).where(AppUser.email.ilike(patron)).scalar_subquery()
    return or_(
        VacacionesAuditLogModel.accion.ilike(patron),
        VacacionesAuditLogModel.entidad.ilike(patron),
        VacacionesAuditLogModel.user_id.in_(emails),
    )


# Etiquetas que muestra la pantalla (`frontend/.../vacaciones/lib/auditoria.ts`):
# se ordena por ellas y no por el código legacy en inglés, para que el orden
# coincida con lo que se lee. Un código sin etiqueta ordena por sí mismo.
_ETIQUETA_ACCION = {
    "CREATE": "Creación",
    "UPDATE": "Edición",
    "DELETE": "Eliminación",
    "APPROVE": "Aprobación",
    "REJECT": "Rechazo",
    "IMPORT": "Importación",
    "LOGIN": "Login",
    "RESET_PASSWORD": "Reset clave",
}
_ETIQUETA_ENTIDAD = {
    "VacationRequest": "Solicitud",
    "Absence": "Baja",
    "Employee": "Empleado",
    "Department": "Sector",
    "Position": "Cargo",
    "Holiday": "Feriado",
    "SystemConfig": "Configuración",
    "User": "Usuario",
}


def _columna_orden(campo: str) -> ColumnElement[Any]:
    log = VacacionesAuditLogModel
    if campo == "accion":
        return case(_ETIQUETA_ACCION, value=log.accion, else_=log.accion)
    if campo == "entidad":
        return case(_ETIQUETA_ENTIDAD, value=log.entidad, else_=log.entidad)
    if campo == "usuario":
        return select(AppUser.email).where(AppUser.id == log.user_id).scalar_subquery()
    return log.created_at.expression


def _clausulas_orden(orden: OrdenAuditoria) -> list[ColumnElement[Any]]:
    """Columna pedida (vacíos al final) y, de desempate, más nuevo primero."""
    columna = _columna_orden(orden.campo)
    principal = columna.desc() if orden.descendente else columna.asc()
    return [
        principal.nulls_last(),
        VacacionesAuditLogModel.created_at.desc(),
        VacacionesAuditLogModel.id.asc(),
    ]


class SqlAlchemyAuditoriaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_pagina(
        self,
        filtros: FiltrosAuditoria,
        *,
        offset: int,
        limit: int,
        orden: OrdenAuditoria = ORDEN_POR_DEFECTO,
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
                    base.order_by(*_clausulas_orden(orden))
                    .offset(offset)
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return [_to_entity(r) for r in rows], total
