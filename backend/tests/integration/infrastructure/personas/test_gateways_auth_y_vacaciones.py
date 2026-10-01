"""Escrituras de Personas en las cuentas (auth) y en las fichas (vacaciones)."""

import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.value_objects.permission_set import PermissionSet
from src.modules.auth.domain.well_known_permissions import MANAGE_ADMIN
from src.modules.auth.infrastructure.models.permission_models import Action, Module, ModuleAction
from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.auth.infrastructure.repositories.sqlalchemy_permission_repository import (
    SqlAlchemyPermissionRepository,
)
from src.modules.personas.domain.entities.persona import DatosPersona
from src.modules.personas.domain.errors import PersonaNoEncontradaError
from src.modules.personas.infrastructure.auth.cuentas_gateway import AuthCuentasGateway
from src.modules.personas.infrastructure.vacaciones.sqlalchemy_fichas_gateway import (
    SqlAlchemyFichasGateway,
)
from src.modules.vacaciones.infrastructure.models.audit_log_model import VacacionesAuditLogModel
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)
from tests.integration.infrastructure.personas.conftest import alta_empleado, crear_usuario


def _datos(email: str) -> DatosPersona:
    return DatosPersona(first_name="Ana", last_name="Paz", email=email, color="#112233")


async def _cuenta(db: AsyncSession, user_id: uuid.UUID) -> AppUser:
    cuenta = await db.get(AppUser, user_id)
    assert cuenta is not None
    await db.refresh(cuenta)
    return cuenta


async def test_crear_y_actualizar_datos_de_la_cuenta(db_session: AsyncSession) -> None:
    gateway = AuthCuentasGateway(db_session)
    email = f"{uuid.uuid4().hex[:8]}@canal.com"

    user_id = await gateway.crear(_datos(email))
    await gateway.actualizar_datos(user_id, _datos(f"nuevo-{email}"))

    cuenta = await _cuenta(db_session, user_id)
    esperado = (f"nuevo-{email}", "Ana Paz", "#112233")
    assert (cuenta.email, cuenta.full_name, cuenta.color) == esperado
    assert await gateway.email_en_uso(f"nuevo-{email}", excepto=None)
    assert not await gateway.email_en_uso(f"nuevo-{email}", excepto=user_id)


async def test_activar_y_desactivar(db_session: AsyncSession) -> None:
    gateway = AuthCuentasGateway(db_session)
    user_id = await crear_usuario(db_session)

    await gateway.desactivar(user_id)
    assert not (await _cuenta(db_session, user_id)).is_active
    await gateway.activar(user_id)
    assert (await _cuenta(db_session, user_id)).is_active


async def _catalogo_admin_manage(db: AsyncSession) -> None:
    if await db.get(Module, "admin") is None:
        db.add(Module(key="admin", label="Administración", route="/admin", icon="shield"))
    if await db.get(Action, "manage") is None:
        db.add(Action(key="manage", label="Administrar"))
    await db.flush()
    if await db.get(ModuleAction, ("admin", "manage")) is None:
        db.add(ModuleAction(module_key="admin", action_key="manage"))
    await db.flush()


async def test_es_privilegiada_superadmin_o_admin_manage(db_session: AsyncSession) -> None:
    await _catalogo_admin_manage(db_session)
    gateway = AuthCuentasGateway(db_session)
    comun = await crear_usuario(db_session)
    superadmin = await crear_usuario(db_session, superadmin=True)
    admin = await crear_usuario(db_session)
    await SqlAlchemyPermissionRepository(db_session).replace_for_user(
        admin, PermissionSet(granted=frozenset({MANAGE_ADMIN})), granted_by=superadmin
    )

    assert not await gateway.es_privilegiada(comun)
    assert await gateway.es_privilegiada(superadmin)
    assert await gateway.es_privilegiada(admin)


async def test_ficha_actualiza_datos_vincula_cuenta_y_audita(
    db_session: AsyncSession, sector_id: uuid.UUID, cargo_id: uuid.UUID
) -> None:
    actor = await crear_usuario(db_session)
    empleado = await alta_empleado(db_session, sector_id, cargo_id)
    gateway = SqlAlchemyFichasGateway(db_session, actor)
    cuenta = await crear_usuario(db_session)
    nuevo = f"{uuid.uuid4().hex[:8]}@canal.com"

    await gateway.actualizar_datos(empleado.id, _datos(nuevo))
    await gateway.vincular_cuenta(empleado.id, cuenta)

    ficha = await SqlAlchemyEmpleadoRepository(db_session).get_by_id(empleado.id)
    assert ficha is not None and (ficha.email, ficha.user_id) == (nuevo, cuenta)
    auditorias = await db_session.scalar(
        select(func.count())
        .select_from(VacacionesAuditLogModel)
        .where(VacacionesAuditLogModel.entidad_id == str(empleado.id))
    )
    assert auditorias == 2


async def test_ficha_email_en_uso_ignora_mayusculas_y_la_propia(
    db_session: AsyncSession, sector_id: uuid.UUID, cargo_id: uuid.UUID
) -> None:
    empleado = await alta_empleado(db_session, sector_id, cargo_id)
    gateway = SqlAlchemyFichasGateway(db_session, None)

    assert await gateway.email_en_uso(empleado.email.upper(), excepto=uuid.uuid4())
    assert not await gateway.email_en_uso(empleado.email, excepto=empleado.id)


async def test_ficha_inexistente(db_session: AsyncSession) -> None:
    with pytest.raises(PersonaNoEncontradaError):
        await SqlAlchemyFichasGateway(db_session, None).vincular_cuenta(uuid.uuid4(), uuid.uuid4())
