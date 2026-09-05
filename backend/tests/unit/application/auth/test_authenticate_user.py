import pytest

from src.modules.auth.application.dtos.commands import LoginCommand
from src.modules.auth.application.use_cases.authenticate_user import (
    AuthenticateUser,
    AuthenticateUserDependencies,
)
from src.modules.auth.domain.errors import (
    AccountDisabledError,
    InvalidCredentialsError,
    TooManyAttemptsError,
)
from tests.unit.application.auth.fakes import (
    DUMMY_HASH,
    FakeLoginAttemptRepository,
    FakePasswordHasher,
    FakePermissionRepository,
    FakeSessionRepository,
    FakeSessionTokenGenerator,
    FakeUserRepository,
    make_user,
)


def _deps(
    users: FakeUserRepository,
    *,
    sessions: FakeSessionRepository | None = None,
    attempts: FakeLoginAttemptRepository | None = None,
    hasher: FakePasswordHasher | None = None,
) -> AuthenticateUserDependencies:
    return AuthenticateUserDependencies(
        users=users,
        sessions=sessions or FakeSessionRepository(),
        permissions=FakePermissionRepository(),
        login_attempts=attempts or FakeLoginAttemptRepository(),
        hasher=hasher or FakePasswordHasher(),
        tokens=FakeSessionTokenGenerator(),
    )


def _command(email: str = "ana@canaldirecto.com.ar", password: str = "Correcta1!") -> LoginCommand:
    return LoginCommand(email=email, password=password, ip="10.0.0.1", user_agent="tests")


async def test_login_valido_abre_sesion_y_registra_intento_exitoso() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    sessions = FakeSessionRepository()
    attempts = FakeLoginAttemptRepository()

    result = await AuthenticateUser(_deps(users, sessions=sessions, attempts=attempts)).execute(
        _command()
    )

    assert result.session_token == "tok"
    assert result.identity.user.id == user.id
    persisted = list(sessions.rows.values())
    assert len(persisted) == 1
    assert persisted[0].user_id == user.id
    assert persisted[0].token_hash == b"h:tok"
    assert attempts.records == [("ana@canaldirecto.com.ar", "10.0.0.1", True)]


async def test_la_sesion_guarda_ip_y_user_agent_del_login() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    sessions = FakeSessionRepository()

    await AuthenticateUser(_deps(users, sessions=sessions)).execute(_command())

    session = next(iter(sessions.rows.values()))
    assert session.ip == "10.0.0.1"
    assert session.user_agent == "tests"


async def test_password_incorrecto_registra_fallo_y_rechaza() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    attempts = FakeLoginAttemptRepository()

    with pytest.raises(InvalidCredentialsError):
        await AuthenticateUser(_deps(users, attempts=attempts)).execute(
            _command(password="Otra1!aa")
        )

    assert attempts.records == [("ana@canaldirecto.com.ar", "10.0.0.1", False)]


async def test_email_desconocido_rechaza_sin_revelar_si_existe() -> None:
    with pytest.raises(InvalidCredentialsError):
        await AuthenticateUser(_deps(FakeUserRepository())).execute(_command())


async def test_email_desconocido_verifica_igual_contra_el_hash_dummy() -> None:
    hasher = FakePasswordHasher()

    with pytest.raises(InvalidCredentialsError):
        await AuthenticateUser(_deps(FakeUserRepository(), hasher=hasher)).execute(_command())

    # Mismo costo de argon2 exista o no el usuario (anti-enumeración por timing).
    assert hasher.verified == [DUMMY_HASH]


async def test_cuenta_desactivada_rechaza_aunque_el_password_sea_correcto() -> None:
    users = FakeUserRepository()
    user = make_user(is_active=False)
    users.rows[user.id] = user

    with pytest.raises(AccountDisabledError):
        await AuthenticateUser(_deps(users)).execute(_command())


async def test_rate_limit_bloquea_antes_de_verificar_credenciales() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    attempts = FakeLoginAttemptRepository(recent_failures=5)

    with pytest.raises(TooManyAttemptsError):
        await AuthenticateUser(_deps(users, attempts=attempts)).execute(_command())

    # Bloqueado por rate limit: ni siquiera se registra un intento nuevo.
    assert attempts.records == []


async def test_rate_limit_cuenta_igual_aunque_cambien_las_mayusculas_del_email() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    attempts = FakeLoginAttemptRepository(recent_failures=4)
    use_case = AuthenticateUser(_deps(users, attempts=attempts))

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(_command(email="Ana@CanalDirecto.com.ar", password="Otra1!aa"))
    with pytest.raises(TooManyAttemptsError):
        await use_case.execute(_command(email="ANA@canaldirecto.com.ar"))

    # El guard y el registro consultan el mismo email normalizado.
    assert attempts.queried_emails == ["ana@canaldirecto.com.ar"] * 2
    assert attempts.records == [("ana@canaldirecto.com.ar", "10.0.0.1", False)]
