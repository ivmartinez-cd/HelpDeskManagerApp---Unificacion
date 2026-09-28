"""RevokeSession, CreateUser y UpdateUser."""

import uuid

import pytest

from src.modules.auth.application.use_cases.create_user import (
    CreateUser,
    CreateUserDependencies,
)
from src.modules.auth.application.use_cases.revoke_session import (
    RevokeSession,
    RevokeSessionDependencies,
)
from src.modules.auth.application.use_cases.update_user import (
    UpdateUser,
    UpdateUserDependencies,
)
from src.modules.auth.domain.errors import (
    EmailAlreadyRegisteredError,
    LastSuperadminError,
    UserNotFoundError,
)
from tests.unit.application.auth.fakes import (
    FakePasswordHasher,
    FakeSessionRepository,
    FakeSessionTokenGenerator,
    FakeUserRepository,
    make_session,
    make_user,
)


async def test_revoke_session_revoca_la_sesion_del_token() -> None:
    sessions = FakeSessionRepository()
    session = make_session(user_id=uuid.uuid4())
    sessions.rows[session.id] = session
    deps = RevokeSessionDependencies(sessions=sessions, tokens=FakeSessionTokenGenerator())

    await RevokeSession(deps).execute("tok")

    assert session.revoked_at is not None
    assert sessions.saved == [session]


async def test_revoke_session_con_token_desconocido_es_noop() -> None:
    sessions = FakeSessionRepository()
    deps = RevokeSessionDependencies(sessions=sessions, tokens=FakeSessionTokenGenerator())

    await RevokeSession(deps).execute("tok")

    assert sessions.saved == []


def _create_deps(users: FakeUserRepository) -> CreateUserDependencies:
    return CreateUserDependencies(users=users, hasher=FakePasswordHasher())


async def test_create_user_da_de_alta_activo_con_el_color_recibido() -> None:
    users = FakeUserRepository()

    user = await CreateUser(_create_deps(users)).execute(
        email="ana@canaldirecto.com.ar", full_name="Ana Prueba", color="#888200"
    )

    assert users.rows[user.id] is user
    assert user.is_active and not user.is_superadmin
    assert user.color == "#888200"


async def test_create_user_sin_color_queda_sin_color() -> None:
    user = await CreateUser(_create_deps(FakeUserRepository())).execute(
        email="ana@canaldirecto.com.ar", full_name="Ana Prueba"
    )
    assert user.color is None


async def test_create_user_rechaza_email_duplicado() -> None:
    users = FakeUserRepository()
    existente = make_user()
    users.rows[existente.id] = existente

    with pytest.raises(EmailAlreadyRegisteredError):
        await CreateUser(_create_deps(users)).execute(
            email=existente.email.value, full_name="Otra Persona"
        )


async def test_update_user_inexistente() -> None:
    with pytest.raises(UserNotFoundError):
        await UpdateUser(UpdateUserDependencies(users=FakeUserRepository())).execute(
            user_id=uuid.uuid4(), full_name="X", is_active=None
        )


async def test_update_user_actualiza_solo_los_campos_presentes() -> None:
    users = FakeUserRepository()
    user = make_user(color="#111111")
    users.rows[user.id] = user

    updated = await UpdateUser(UpdateUserDependencies(users=users)).execute(
        user_id=user.id, full_name="Nuevo Nombre", is_active=None, color="#222222"
    )

    assert updated.full_name == "Nuevo Nombre"
    assert updated.color == "#222222"
    assert updated.is_active is True
    assert users.saved == [user]


async def test_no_se_puede_desactivar_al_ultimo_superadmin() -> None:
    users = FakeUserRepository()
    admin = make_user(is_superadmin=True)
    users.rows[admin.id] = admin

    with pytest.raises(LastSuperadminError):
        await UpdateUser(UpdateUserDependencies(users=users)).execute(
            user_id=admin.id, full_name=None, is_active=False
        )


async def test_desactivar_un_superadmin_con_otro_activo_esta_permitido() -> None:
    users = FakeUserRepository()
    admin = make_user(is_superadmin=True)
    otro = make_user(email="otro@canaldirecto.com.ar", is_superadmin=True)
    users.rows[admin.id] = admin
    users.rows[otro.id] = otro

    updated = await UpdateUser(UpdateUserDependencies(users=users)).execute(
        user_id=admin.id, full_name=None, is_active=False
    )

    assert updated.is_active is False
