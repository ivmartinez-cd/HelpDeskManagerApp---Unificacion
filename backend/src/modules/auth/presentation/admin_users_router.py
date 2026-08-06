import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.application.use_cases.create_user import CreateUser, CreateUserDependencies
from src.modules.auth.application.use_cases.request_password_reset import (
    RequestPasswordReset,
    RequestPasswordResetDependencies,
)
from src.modules.auth.application.use_cases.update_user import UpdateUser, UpdateUserDependencies
from src.modules.auth.domain.errors import UserNotFoundError
from src.modules.auth.domain.well_known_permissions import MANAGE_ADMIN
from src.modules.auth.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from src.modules.auth.infrastructure.mailer_factory import get_mailer
from src.modules.auth.infrastructure.repositories.sqlalchemy_reset_token_repository import (
    SqlAlchemyResetTokenRepository,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from src.modules.auth.infrastructure.secure_token_generator import SecureTokenGenerator
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.auth.presentation.schemas.admin_user_schemas import (
    AdminUserResponse,
    CreateUserRequest,
    PaginatedUsersResponse,
    UpdateUserRequest,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/admin/users", tags=["admin"])

_require_manage_admin = Depends(require_permission(MANAGE_ADMIN))
_MAX_PAGE_SIZE = 100


@router.get("")
async def list_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=_MAX_PAGE_SIZE),
    q: str | None = Query(default=None),
    _: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
) -> PaginatedUsersResponse:
    users, total = await SqlAlchemyUserRepository(db).list_page(page=page, size=size, query=q)
    items = [AdminUserResponse.from_domain(user) for user in users]
    return PaginatedUsersResponse(items=items, total=total, page=page, size=size)


@router.get("/{user_id}")
async def get_user(
    user_id: uuid.UUID,
    _: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    user = await SqlAlchemyUserRepository(db).get_by_id(user_id)
    if user is None:
        raise UserNotFoundError()
    return AdminUserResponse.from_domain(user)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserRequest,
    _: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    deps = CreateUserDependencies(
        users=SqlAlchemyUserRepository(db), hasher=Argon2PasswordHasher()
    )
    user = await CreateUser(deps).execute(email=payload.email, full_name=payload.full_name)
    await _send_activation_link(db, user_email=user.email.value)
    return AdminUserResponse.from_domain(user)


@router.patch("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    payload: UpdateUserRequest,
    _: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    deps = UpdateUserDependencies(users=SqlAlchemyUserRepository(db))
    user = await UpdateUser(deps).execute(
        user_id=user_id, full_name=payload.full_name, is_active=payload.is_active
    )
    return AdminUserResponse.from_domain(user)


@router.post("/{user_id}/password-reset", status_code=status.HTTP_202_ACCEPTED)
async def trigger_password_reset(
    user_id: uuid.UUID,
    _: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    user = await SqlAlchemyUserRepository(db).get_by_id(user_id)
    if user is None:
        raise UserNotFoundError()
    await _send_activation_link(db, user_email=user.email.value)
    return {"message": "Se envió un link para restablecer la contraseña."}


async def _send_activation_link(db: AsyncSession, *, user_email: str) -> None:
    settings = get_settings()
    deps = RequestPasswordResetDependencies(
        users=SqlAlchemyUserRepository(db),
        reset_tokens=SqlAlchemyResetTokenRepository(db),
        tokens=SecureTokenGenerator(),
        mailer=get_mailer(),
        frontend_url=settings.frontend_url,
    )
    await RequestPasswordReset(deps).execute(user_email)
