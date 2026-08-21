"""Construcción del ActorVacaciones (D4 del plan): proyecta la Identity de
auth al vocabulario del módulo. Es el único lugar de vacaciones que mira
grants; domain/application reciben el dataclass ya resuelto."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity, PermissionView
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_sector_manager_repository import (  # noqa: E501
    SqlAlchemySectorManagerRepository,
)
from src.shared.infrastructure.database.session import get_db

_MANAGE = PermissionView(module="vacaciones", action="manage")


async def get_actor_vacaciones(
    identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ActorVacaciones:
    es_admin = identity.user.is_superadmin or _MANAGE in identity.permissions
    sector = await SqlAlchemySectorManagerRepository(db).get_sector_de_usuario(
        identity.user.id
    )
    empleado = await SqlAlchemyEmpleadoRepository(db).get_by_user_id(identity.user.id)
    return ActorVacaciones(
        user_id=identity.user.id,
        es_admin=es_admin,
        sector_gestionado_id=sector,
        empleado_id=empleado.id if empleado else None,
    )
