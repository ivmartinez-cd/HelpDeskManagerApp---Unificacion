from src.modules.auth.application.use_cases.request_password_reset import (
    RequestPasswordReset,
    RequestPasswordResetDependencies,
)
from tests.unit.application.auth.fakes import (
    FakeMailer,
    FakeResetTokenRepository,
    FakeSessionTokenGenerator,
    FakeUserRepository,
    make_user,
)


def _deps(
    users: FakeUserRepository, tokens_repo: FakeResetTokenRepository, mailer: FakeMailer
) -> RequestPasswordResetDependencies:
    return RequestPasswordResetDependencies(
        users=users,
        reset_tokens=tokens_repo,
        tokens=FakeSessionTokenGenerator(),
        mailer=mailer,
        frontend_url="http://front",
    )


async def test_email_desconocido_no_manda_nada_ni_persiste_token() -> None:
    tokens_repo = FakeResetTokenRepository()
    mailer = FakeMailer()

    await RequestPasswordReset(_deps(FakeUserRepository(), tokens_repo, mailer)).execute(
        "nadie@canaldirecto.com.ar"
    )

    assert mailer.sent == []
    assert tokens_repo.rows == {}


async def test_reset_persiste_token_hasheado_y_manda_el_link() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    tokens_repo = FakeResetTokenRepository()
    mailer = FakeMailer()

    await RequestPasswordReset(_deps(users, tokens_repo, mailer)).execute(user.email.value)

    assert list(tokens_repo.rows) == [b"h:tok"]
    assert tokens_repo.rows[b"h:tok"].user_id == user.id
    assert len(mailer.sent) == 1
    assert mailer.sent[0].to == user.email.value
    assert "http://front/reset-password?token=tok" in mailer.sent[0].body
    assert "&new=1" not in mailer.sent[0].body
    assert "Restablecer" in mailer.sent[0].subject


async def test_activation_usa_asunto_propio_y_marca_el_link_como_nuevo() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    mailer = FakeMailer()

    await RequestPasswordReset(_deps(users, FakeResetTokenRepository(), mailer)).execute(
        user.email.value, purpose="activation"
    )

    assert "Activá" in mailer.sent[0].subject
    assert "token=tok&new=1" in mailer.sent[0].body
