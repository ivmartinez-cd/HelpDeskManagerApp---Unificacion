from src.modules.auth.application.use_cases.request_password_reset import (
    RequestPasswordReset,
    RequestPasswordResetDependencies,
)
from tests.unit.application.auth.fakes import (
    FakeResetTokenRepository,
    FakeSessionTokenGenerator,
    FakeUserRepository,
    make_user,
)


def _deps(
    users: FakeUserRepository, tokens_repo: FakeResetTokenRepository
) -> RequestPasswordResetDependencies:
    return RequestPasswordResetDependencies(
        users=users,
        reset_tokens=tokens_repo,
        tokens=FakeSessionTokenGenerator(),
        frontend_url="http://front",
    )


async def test_email_desconocido_no_arma_mail_ni_persiste_token() -> None:
    tokens_repo = FakeResetTokenRepository()

    mail = await RequestPasswordReset(_deps(FakeUserRepository(), tokens_repo)).execute(
        "nadie@canaldirecto.com.ar"
    )

    assert mail is None
    assert tokens_repo.rows == {}


async def test_reset_persiste_token_hasheado_y_devuelve_el_mail_con_el_link() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    tokens_repo = FakeResetTokenRepository()

    mail = await RequestPasswordReset(_deps(users, tokens_repo)).execute(user.email.value)

    assert list(tokens_repo.rows) == [b"h:tok"]
    assert tokens_repo.rows[b"h:tok"].user_id == user.id
    assert mail is not None
    assert mail.to == user.email.value
    assert "http://front/reset-password?token=tok" in mail.body
    assert "&new=1" not in mail.body
    assert "Restablecer" in mail.subject


async def test_activation_usa_asunto_propio_y_marca_el_link_como_nuevo() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user

    mail = await RequestPasswordReset(_deps(users, FakeResetTokenRepository())).execute(
        user.email.value, purpose="activation"
    )

    assert mail is not None
    assert "Activá" in mail.subject
    assert "token=tok&new=1" in mail.body


async def test_usuario_inactivo_no_recibe_token_ni_mail() -> None:
    users = FakeUserRepository()
    user = make_user(is_active=False)
    users.rows[user.id] = user
    tokens_repo = FakeResetTokenRepository()

    mail = await RequestPasswordReset(_deps(users, tokens_repo)).execute(user.email.value)

    assert mail is None
    assert tokens_repo.rows == {}


async def test_mas_de_tres_pedidos_en_la_ventana_no_emiten_otro_token() -> None:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    tokens_repo = FakeResetTokenRepository()
    use_case = RequestPasswordReset(_deps(users, tokens_repo))

    emitidos = [await use_case.execute(user.email.value) for _ in range(4)]

    assert [m is not None for m in emitidos] == [True, True, True, False]
    assert len(tokens_repo.created) == 3
