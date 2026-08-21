from fastapi import APIRouter, Depends, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.commands import LoginCommand
from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.application.use_cases.authenticate_user import (
    AuthenticateUser,
    AuthenticateUserDependencies,
)
from src.modules.auth.application.use_cases.change_password import (
    ChangePassword,
    ChangePasswordDependencies,
)
from src.modules.auth.application.use_cases.list_visible_modules import (
    ListVisibleModules,
    ListVisibleModulesDependencies,
)
from src.modules.auth.application.use_cases.request_password_reset import (
    RequestPasswordReset,
    RequestPasswordResetDependencies,
)
from src.modules.auth.application.use_cases.reset_password import (
    ResetPassword,
    ResetPasswordDependencies,
)
from src.modules.auth.application.use_cases.revoke_session import (
    RevokeSession,
    RevokeSessionDependencies,
)
from src.modules.auth.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from src.modules.auth.infrastructure.mailer_factory import get_mailer
from src.modules.auth.infrastructure.repositories.sqlalchemy_login_attempt_repository import (
    SqlAlchemyLoginAttemptRepository,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_module_catalog_repository import (
    SqlAlchemyModuleCatalogRepository,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_permission_repository import (
    SqlAlchemyPermissionRepository,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_reset_token_repository import (
    SqlAlchemyResetTokenRepository,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_session_repository import (
    SqlAlchemySessionRepository,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from src.modules.auth.infrastructure.secure_token_generator import SecureTokenGenerator
from src.modules.auth.presentation.cookies import clear_session_cookies, set_session_cookies
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.modules.auth.presentation.schemas.catalog_schemas import ModuleCatalogResponse
from src.modules.auth.presentation.schemas.identity_schemas import IdentityResponse
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> IdentityResponse:
    tokens = SecureTokenGenerator()
    deps = AuthenticateUserDependencies(
        users=SqlAlchemyUserRepository(db),
        sessions=SqlAlchemySessionRepository(db),
        permissions=SqlAlchemyPermissionRepository(db),
        login_attempts=SqlAlchemyLoginAttemptRepository(db),
        hasher=Argon2PasswordHasher(),
        tokens=tokens,
    )
    command = LoginCommand(
        email=payload.email,
        password=payload.password,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    result = await AuthenticateUser(deps).execute(command)
    # La sesión queda commiteada antes de que salga la respuesta porque `get_db`
    # se declara con scope="function" (ADR-030). Con el scope por defecto el
    # cliente recibía la cookie y pegaba a /api/auth/me antes del commit → 401.
    set_session_cookies(response, session_token=result.session_token, csrf_token=tokens.generate())
    return IdentityResponse.from_domain(result.identity)


@router.get("/me")
async def me(identity: Identity = Depends(get_current_identity)) -> IdentityResponse:
    return IdentityResponse.from_domain(identity)


@router.get("/modules")
async def my_modules(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=200, ge=1, le=500),
    identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[ModuleCatalogResponse]:
    """Arma el sidebar: a diferencia de /admin/catalog/modules (que requiere
    admin:manage y expone todo el catálogo para editar la matriz), esto es
    para cualquier usuario autenticado y ya viene filtrado a lo que puede ver."""
    deps = ListVisibleModulesDependencies(
        catalog=SqlAlchemyModuleCatalogRepository(db),
        permissions=SqlAlchemyPermissionRepository(db),
    )
    entries = await ListVisibleModules(deps).execute(
        user_id=identity.user.id, is_superadmin=identity.user.is_superadmin
    )
    return Page.of(
        [ModuleCatalogResponse.from_domain(entry) for entry in entries], page=page, size=size
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request, response: Response, db: AsyncSession = Depends(get_db, scope="function")
) -> None:
    token = request.cookies.get(get_settings().session_cookie_name)
    if token:
        deps = RevokeSessionDependencies(
            sessions=SqlAlchemySessionRepository(db), tokens=SecureTokenGenerator()
        )
        await RevokeSession(deps).execute(token)
    clear_session_cookies(response)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


_FORGOT_PASSWORD_MESSAGE = (
    "Si el email existe, vas a recibir instrucciones para restablecer tu contraseña."
)


@router.post("/password/forgot", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db, scope="function")
) -> dict[str, str]:
    settings = get_settings()
    deps = RequestPasswordResetDependencies(
        users=SqlAlchemyUserRepository(db),
        reset_tokens=SqlAlchemyResetTokenRepository(db),
        tokens=SecureTokenGenerator(),
        mailer=get_mailer(),
        frontend_url=settings.frontend_url,
    )
    await RequestPasswordReset(deps).execute(payload.email)
    return {"message": _FORGOT_PASSWORD_MESSAGE}


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    token: str
    new_password: str = Field(alias="newPassword")


@router.post("/password/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db, scope="function")
) -> None:
    deps = ResetPasswordDependencies(
        users=SqlAlchemyUserRepository(db),
        reset_tokens=SqlAlchemyResetTokenRepository(db),
        sessions=SqlAlchemySessionRepository(db),
        hasher=Argon2PasswordHasher(),
        tokens=SecureTokenGenerator(),
    )
    await ResetPassword(deps).execute(raw_token=payload.token, new_password=payload.new_password)


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    current_password: str = Field(alias="currentPassword")
    new_password: str = Field(alias="newPassword")


@router.post("/password/change", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    deps = ChangePasswordDependencies(
        users=SqlAlchemyUserRepository(db),
        sessions=SqlAlchemySessionRepository(db),
        hasher=Argon2PasswordHasher(),
    )
    await ChangePassword(deps).execute(
        user_id=identity.user.id,
        current_password=payload.current_password,
        new_password=payload.new_password,
        keep_session_id=identity.session_id,
    )
