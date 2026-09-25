"""Armado de dependencias del módulo: funciones de módulo para que los tests de
router las reemplacen con fakes."""

import uuid

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.personas.application.use_cases.actualizar_datos_persona import (
    ActualizarDatosDependencies,
)
from src.modules.personas.application.use_cases.gestionar_acceso import AccesoDependencies
from src.modules.personas.domain.repositories.cuentas_gateway import CuentasGateway
from src.modules.personas.domain.repositories.persona_repository import PersonaRepository
from src.modules.personas.infrastructure.auth.cuentas_gateway import AuthCuentasGateway
from src.modules.personas.infrastructure.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)
from src.modules.personas.infrastructure.vacaciones.sqlalchemy_fichas_gateway import (
    SqlAlchemyFichasGateway,
)
from src.modules.personas.presentation.aviso_activacion import MailAvisoActivacion


def repositorio(db: AsyncSession) -> PersonaRepository:
    return SqlAlchemyPersonaRepository(db)


def cuentas(db: AsyncSession) -> CuentasGateway:
    return AuthCuentasGateway(db)


def deps_datos(db: AsyncSession, actor_id: uuid.UUID) -> ActualizarDatosDependencies:
    return ActualizarDatosDependencies(
        personas=repositorio(db),
        fichas=SqlAlchemyFichasGateway(db, actor_id),
        cuentas=cuentas(db),
    )


def deps_acceso(
    db: AsyncSession, actor_id: uuid.UUID, background_tasks: BackgroundTasks
) -> AccesoDependencies:
    return AccesoDependencies(
        personas=repositorio(db),
        fichas=SqlAlchemyFichasGateway(db, actor_id),
        cuentas=cuentas(db),
        aviso=MailAvisoActivacion(db, background_tasks),
    )
