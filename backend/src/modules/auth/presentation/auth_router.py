from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.commands import LoginCommand
from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.application.use_cases.authenticate_user import (
    AuthenticateUser,
    AuthenticateUserDependencies,
)
from src.modules.auth.application.use_cases.revoke_session import (
    RevokeSession,
    RevokeSessionDependencies,
)
from src.modules.auth.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from src.modules.auth.infrastructure.repositories.sqlalchemy_login_attempt_repository import (
    SqlAlchemyLoginAttemptRepository,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_permission_repository import (
    SqlAlchemyPermissionRepository,
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
from src.modules.auth.presentation.schemas.identity_schemas import IdentityResponse
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
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
    set_session_cookies(response, session_token=result.session_token, csrf_token=tokens.generate())
    return IdentityResponse.from_domain(result.identity)


@router.get("/me")
async def me(identity: Identity = Depends(get_current_identity)) -> IdentityResponse:
    return IdentityResponse.from_domain(identity)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> None:
    token = request.cookies.get(get_settings().session_cookie_name)
    if token:
        deps = RevokeSessionDependencies(
            sessions=SqlAlchemySessionRepository(db), tokens=SecureTokenGenerator()
        )
        await RevokeSession(deps).execute(token)
    clear_session_cookies(response)
