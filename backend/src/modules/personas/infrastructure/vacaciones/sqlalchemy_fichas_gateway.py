"""Escribe en la ficha de empleado de Gestión de Personal (`vacaciones`) —
dependencia cross-module a propósito, solo en infrastructure (ADR-040). Deja la
misma entrada de auditoría que el ABM de empleados."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.personas.domain.entities.persona import DatosPersona
from src.modules.personas.domain.errors import PersonaNoEncontradaError
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.registro_auditoria import (
    ACCION_UPDATE,
    ENTIDAD_EMPLEADO,
)
from src.modules.vacaciones.infrastructure.models.empleado_model import VacacionesEmpleadoModel
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_auditoria import (
    SqlAlchemyRegistradorAuditoria,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)


class SqlAlchemyFichasGateway:
    def __init__(self, session: AsyncSession, actor_user_id: uuid.UUID | None) -> None:
        self._session = session
        self._empleados = SqlAlchemyEmpleadoRepository(session)
        self._auditoria = SqlAlchemyRegistradorAuditoria(session, actor_user_id)

    async def email_en_uso(self, email: str, *, excepto: uuid.UUID) -> bool:
        stmt = select(VacacionesEmpleadoModel.id).where(
            func.lower(VacacionesEmpleadoModel.email) == email.lower(),
            VacacionesEmpleadoModel.id != excepto,
        )
        return (await self._session.execute(stmt)).first() is not None

    async def actualizar_datos(self, persona_id: uuid.UUID, datos: DatosPersona) -> None:
        empleado = await self._get(persona_id)
        empleado.first_name = datos.first_name
        empleado.last_name = datos.last_name
        empleado.email = datos.email
        empleado.color = datos.color
        await self._guardar(empleado)

    async def vincular_cuenta(self, persona_id: uuid.UUID, user_id: uuid.UUID) -> None:
        empleado = await self._get(persona_id)
        empleado.user_id = user_id
        await self._guardar(empleado)

    async def _get(self, persona_id: uuid.UUID) -> Empleado:
        empleado = await self._empleados.get_by_id(persona_id)
        if empleado is None:
            raise PersonaNoEncontradaError(persona_id)
        return empleado

    async def _guardar(self, empleado: Empleado) -> None:
        await self._empleados.save(empleado)
        await self._auditoria.registrar(
            ACCION_UPDATE,
            ENTIDAD_EMPLEADO,
            str(empleado.id),
            {"employee": empleado.nombre_completo, "email": empleado.email},
        )
