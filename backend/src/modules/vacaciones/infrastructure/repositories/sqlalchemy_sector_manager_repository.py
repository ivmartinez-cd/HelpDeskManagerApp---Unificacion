import uuid

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.permission_models import UserModuleScope
from src.modules.vacaciones.domain.repositories.sector_manager_repository import JefeSector

_MODULE_KEY = "vacaciones"


class SqlAlchemySectorManagerRepository:
    """Jefe↔sector sobre `user_module_scope` de auth (D2). Semántica: la fila
    (user, 'vacaciones', department) significa "jefe de ese sector" — dejar
    esto escrito importa porque auth tiene previsto un ScopePolicy real que
    algún día leerá esta misma tabla."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_sector_de_usuario(self, user_id: uuid.UUID) -> uuid.UUID | None:
        stmt = select(UserModuleScope.scope_department_id).where(
            UserModuleScope.user_id == user_id,
            UserModuleScope.module_key == _MODULE_KEY,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_jefes(self) -> list[JefeSector]:
        stmt = select(UserModuleScope).where(
            UserModuleScope.module_key == _MODULE_KEY,
            UserModuleScope.scope_department_id.is_not(None),
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            JefeSector(user_id=r.user_id, department_id=r.scope_department_id)
            for r in rows
            if r.scope_department_id is not None
        ]

    async def asignar(self, user_id: uuid.UUID, department_id: uuid.UUID) -> None:
        stmt = pg_insert(UserModuleScope).values(
            user_id=user_id, module_key=_MODULE_KEY, scope_department_id=department_id
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[UserModuleScope.user_id, UserModuleScope.module_key],
            set_={"scope_department_id": department_id},
        )
        await self._session.execute(stmt)

    async def desasignar(self, user_id: uuid.UUID) -> None:
        stmt = delete(UserModuleScope).where(
            UserModuleScope.user_id == user_id,
            UserModuleScope.module_key == _MODULE_KEY,
        )
        await self._session.execute(stmt)
