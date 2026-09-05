"""ChangePassword y ResetPassword: rotación de hash + revocación de sesiones."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from src.modules.auth.application.use_cases.change_password import (
    ChangePassword,
    ChangePasswordDependencies,
)
from src.modules.auth.application.use_cases.reset_password import (
    ResetPassword,
    ResetPasswordDependencies,
)
from src.modules.auth.domain.entities.password_reset_token import PasswordResetToken
from src.modules.auth.domain.errors import (
    AccountDisabledError,
    InvalidCredentialsError,
    TokenAlreadyUsedError,
    TokenExpiredError,
    TokenInvalidError,
    WeakPasswordError,
)
from tests.unit.application.auth.fakes import (
    FakePasswordHasher,
    FakeResetTokenRepository,
    FakeSessionRepository,
    FakeSessionTokenGenerator,
    FakeUserRepository,
    make_session,
    make_user,
)


def _change_deps(
    users: FakeUserRepository, sessions: FakeSessionRepository
) -> ChangePasswordDependencies:
    return ChangePasswordDependencies(users=users, sessions=sessions, hasher=FakePasswordHasher())


async def test_change_password_rota_el_hash_y_revoca_las_otras_sesiones() -> None:
    users = FakeUserRepository()
    user = make_user(password="Vieja1!a")
    users.rows[user.id] = user
    sessions = FakeSessionRepository()
    actual = make_session(user_id=user.id)

    await ChangePassword(_change_deps(users, sessions)).execute(
        user_id=user.id,
        current_password="Vieja1!a",
        new_password="Nueva1!a",
        keep_session_id=actual.id,
    )

    assert user.password_hash.value == "hash:Nueva1!a"
    assert sessions.revoked_all == [(user.id, actual.id)]


async def test_change_password_rechaza_si_el_password_actual_no_verifica() -> None:
    users = FakeUserRepository()
    user = make_user(password="Vieja1!a")
    users.rows[user.id] = user
    sessions = FakeSessionRepository()

    with pytest.raises(InvalidCredentialsError):
        await ChangePassword(_change_deps(users, sessions)).execute(
            user_id=user.id,
            current_password="NoEsEsa1!",
            new_password="Nueva1!a",
            keep_session_id=uuid.uuid4(),
        )
    assert sessions.revoked_all == []


async def test_change_password_aplica_la_politica_de_fuerza_al_nuevo() -> None:
    users = FakeUserRepository()
    user = make_user(password="Vieja1!a")
    users.rows[user.id] = user

    with pytest.raises(WeakPasswordError):
        await ChangePassword(_change_deps(users, FakeSessionRepository())).execute(
            user_id=user.id,
            current_password="Vieja1!a",
            new_password="corta",
            keep_session_id=uuid.uuid4(),
        )


def _reset_deps(
    users: FakeUserRepository,
    tokens_repo: FakeResetTokenRepository,
    sessions: FakeSessionRepository,
) -> ResetPasswordDependencies:
    return ResetPasswordDependencies(
        users=users,
        reset_tokens=tokens_repo,
        sessions=sessions,
        hasher=FakePasswordHasher(),
        tokens=FakeSessionTokenGenerator(),
    )


def _reset_token(
    user_id: uuid.UUID,
    *,
    expires_delta: timedelta = timedelta(minutes=30),
    used: bool = False,
) -> PasswordResetToken:
    now = datetime.now(UTC)
    return PasswordResetToken(
        id=uuid.uuid4(),
        user_id=user_id,
        token_hash=b"h:tok",
        expires_at=now + expires_delta,
        used_at=now if used else None,
    )


async def test_reset_password_actualiza_quema_el_token_y_revoca_todo() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    tokens_repo = FakeResetTokenRepository()
    record = _reset_token(user.id)
    tokens_repo.rows[record.token_hash] = record
    sessions = FakeSessionRepository()

    await ResetPassword(_reset_deps(users, tokens_repo, sessions)).execute(
        raw_token="tok", new_password="Nueva1!a"
    )

    assert user.password_hash.value == "hash:Nueva1!a"
    assert tokens_repo.marked_used == [b"h:tok"]
    # A diferencia de change-password, acá no se conserva ninguna sesión.
    assert sessions.revoked_all == [(user.id, None)]


async def test_reset_password_token_desconocido() -> None:
    with pytest.raises(TokenInvalidError):
        await ResetPassword(
            _reset_deps(FakeUserRepository(), FakeResetTokenRepository(), FakeSessionRepository())
        ).execute(raw_token="tok", new_password="Nueva1!a")


async def test_reset_password_token_ya_usado() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    tokens_repo = FakeResetTokenRepository()
    record = _reset_token(user.id, used=True)
    tokens_repo.rows[record.token_hash] = record

    with pytest.raises(TokenAlreadyUsedError):
        await ResetPassword(_reset_deps(users, tokens_repo, FakeSessionRepository())).execute(
            raw_token="tok", new_password="Nueva1!a"
        )


async def test_reset_password_token_vencido() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    tokens_repo = FakeResetTokenRepository()
    record = _reset_token(user.id, expires_delta=timedelta(minutes=-1))
    tokens_repo.rows[record.token_hash] = record

    with pytest.raises(TokenExpiredError):
        await ResetPassword(_reset_deps(users, tokens_repo, FakeSessionRepository())).execute(
            raw_token="tok", new_password="Nueva1!a"
        )


async def test_reset_password_de_usuario_inactivo_es_cuenta_deshabilitada() -> None:
    users = FakeUserRepository()
    user = make_user(is_active=False)
    users.rows[user.id] = user
    tokens_repo = FakeResetTokenRepository()
    record = _reset_token(user.id)
    tokens_repo.rows[record.token_hash] = record
    sessions = FakeSessionRepository()

    with pytest.raises(AccountDisabledError):
        await ResetPassword(_reset_deps(users, tokens_repo, sessions)).execute(
            raw_token="tok", new_password="Nueva1!a"
        )

    assert users.saved == []
    assert tokens_repo.marked_used == []


async def test_reset_password_usuario_inexistente_es_token_invalido() -> None:
    tokens_repo = FakeResetTokenRepository()
    record = _reset_token(uuid.uuid4())
    tokens_repo.rows[record.token_hash] = record

    with pytest.raises(TokenInvalidError):
        await ResetPassword(
            _reset_deps(FakeUserRepository(), tokens_repo, FakeSessionRepository())
        ).execute(raw_token="tok", new_password="Nueva1!a")
