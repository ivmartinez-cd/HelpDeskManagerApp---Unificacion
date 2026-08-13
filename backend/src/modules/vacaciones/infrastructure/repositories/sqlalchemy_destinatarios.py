"""Destinatarios del aviso de nueva solicitud (paridad del legacy: MANAGERs del
sector del empleado + todos los ADMINs, deduplicados). En esta plataforma eso
es: usuarios con scope de jefe sobre el sector (`user_module_scope`, D2) +
usuarios con grant `manage` del módulo. Solo cuentas activas (el legacy no
tenía noción de cuenta inactiva)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.permission_models import (
    PermissionGrant,
    UserModuleScope,
)
from src.modules.auth.infrastructure.models.user_model import AppUser

_MODULE_KEY = "vacaciones"
_ADMIN_ACTION_KEY = "manage"


class SqlAlchemyDestinatariosNuevaSolicitud:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def emails(self, department_id: uuid.UUID) -> list[str]:
        jefes = select(AppUser.email).join(
            UserModuleScope, UserModuleScope.user_id == AppUser.id
        ).where(
            UserModuleScope.module_key == _MODULE_KEY,
            UserModuleScope.scope_department_id == department_id,
            AppUser.is_active.is_(True),
        )
        admins = select(AppUser.email).join(
            PermissionGrant, PermissionGrant.user_id == AppUser.id
        ).where(
            PermissionGrant.module_key == _MODULE_KEY,
            PermissionGrant.action_key == _ADMIN_ACTION_KEY,
            AppUser.is_active.is_(True),
        )
        emails_jefes = (await self._session.execute(jefes)).scalars().all()
        emails_admins = (await self._session.execute(admins)).scalars().all()
        return list(dict.fromkeys([*emails_jefes, *emails_admins]))
