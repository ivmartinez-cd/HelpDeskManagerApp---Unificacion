from datetime import timedelta

import pytest

from src.modules.auth.application.use_cases.get_current_identity import (
    GetCurrentIdentity,
    GetCurrentIdentityDependencies,
)
from src.modules.auth.domain.errors import NotAuthenticatedError
from tests.unit.application.auth.fakes import (
    FakePermissionRepository,
    FakeSessionRepository,
    FakeSessionTokenGenerator,
    FakeUserRepository,
    make_session,
    make_user,
)


def _deps(
    users: FakeUserRepository, sessions: FakeSessionRepository
) -> GetCurrentIdentityDependencies:
    return GetCurrentIdentityDependencies(
        sessions=sessions,
        users=users,
        permissions=FakePermissionRepository(),
        tokens=FakeSessionTokenGenerator(),
    )


async def test_sesion_fresca_devuelve_identidad_sin_tocar_la_sesion() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    sessions = FakeSessionRepository()
    session = make_session(user_id=user.id, last_seen_delta=timedelta(minutes=5))
    sessions.rows[session.id] = session

    identity = await GetCurrentIdentity(_deps(users, sessions)).execute("tok")

    assert identity.user.id == user.id
    assert identity.session_id == session.id
    # Vencimiento deslizante: <1h desde el último touch, no se escribe nada.
    assert sessions.saved == []


async def test_sesion_vieja_extiende_el_vencimiento_deslizante() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    sessions = FakeSessionRepository()
    # Vencía en 1 día: tras el touch tiene que quedar en now+7d, estrictamente mayor.
    session = make_session(
        user_id=user.id,
        last_seen_delta=timedelta(hours=2),
        expires_delta=timedelta(days=1),
    )
    sessions.rows[session.id] = session
    vencia = session.expires_at

    await GetCurrentIdentity(_deps(users, sessions)).execute("tok")

    assert sessions.saved == [session]
    assert session.expires_at > vencia


async def test_token_desconocido_no_autentica() -> None:
    with pytest.raises(NotAuthenticatedError):
        await GetCurrentIdentity(_deps(FakeUserRepository(), FakeSessionRepository())).execute(
            "tok"
        )


async def test_sesion_revocada_no_autentica() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    sessions = FakeSessionRepository()
    session = make_session(user_id=user.id, revoked=True)
    sessions.rows[session.id] = session

    with pytest.raises(NotAuthenticatedError):
        await GetCurrentIdentity(_deps(users, sessions)).execute("tok")


async def test_usuario_desactivado_no_autentica_aunque_la_sesion_siga_viva() -> None:
    users = FakeUserRepository()
    user = make_user(is_active=False)
    users.rows[user.id] = user
    sessions = FakeSessionRepository()
    session = make_session(user_id=user.id)
    sessions.rows[session.id] = session

    with pytest.raises(NotAuthenticatedError):
        await GetCurrentIdentity(_deps(users, sessions)).execute("tok")
