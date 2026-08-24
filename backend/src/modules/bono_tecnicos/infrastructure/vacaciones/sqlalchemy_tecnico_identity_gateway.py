"""Adapter que resuelve el técnico de Siges de un usuario autenticado
cruzando con el vínculo Empleado↔Siges de Gestión de Personal (`vacaciones`)
— dependencia cross-module a propósito, solo en infrastructure, mismo
criterio que `sqlalchemy_dias_sugeridos_gateway.py`."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.bono_tecnicos.domain.repositories.tecnico_identity_gateway import (
    TecnicoVinculado,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)


class SqlAlchemyTecnicoIdentityGateway:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_por_usuario(self, user_id: uuid.UUID) -> TecnicoVinculado | None:
        empleado = await SqlAlchemyEmpleadoRepository(self._session).get_by_user_id(user_id)
        if empleado is None or empleado.siges_empresa_id is None:
            return None
        return TecnicoVinculado(
            id_tecnico=empleado.siges_empresa_id, tecnico=empleado.nombre_completo
        )
