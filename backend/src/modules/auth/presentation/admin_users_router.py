import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.application.use_cases.request_password_reset import (
    RequestPasswordReset,
    RequestPasswordResetDependencies,
    ResetPurpose,
)
from src.modules.auth.domain.errors import AccountDisabledError, UserNotFoundError
from src.modules.auth.domain.well_known_permissions import MANAGE_ADMIN
from src.modules.auth.infrastructure.mail_logo import get_logo_base64
from src.modules.auth.infrastructure.repositories.sqlalchemy_reset_token_repository import (
    SqlAlchemyResetTokenRepository,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from src.modules.auth.infrastructure.secure_token_generator import SecureTokenGenerator
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.auth.presentation.password_mail import encolar_mail
from src.modules.auth.presentation.schemas.admin_user_schemas import AdminUserResponse
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/admin/users", tags=["admin"])

_require_manage_admin = Depends(require_permission(MANAGE_ADMIN))


@router.get("/{user_id}")
async def get_user(
    user_id: uuid.UUID,
    _: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> AdminUserResponse:
    user = await SqlAlchemyUserRepository(db).get_by_id(user_id)
    if user is None:
        raise UserNotFoundError()
    return AdminUserResponse.from_domain(user)


@router.post("/{user_id}/password-reset", status_code=status.HTTP_202_ACCEPTED)
async def trigger_password_reset(
    user_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    _: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> dict[str, str]:
    user = await SqlAlchemyUserRepository(db).get_by_id(user_id)
    if user is None:
        raise UserNotFoundError()
    # A diferencia del forgot público, acá el admin sí merece saber por qué
    # no sale el mail: el caso de uso lo omitiría en silencio.
    if not user.is_active:
        raise AccountDisabledError()
    await _send_password_link(db, background_tasks, user_email=user.email.value, purpose="reset")
    return {"message": "Se envió un link para restablecer la contraseña."}


async def _send_password_link(
    db: AsyncSession,
    background_tasks: BackgroundTasks,
    *,
    user_email: str,
    purpose: ResetPurpose,
) -> None:
    deps = RequestPasswordResetDependencies(
        users=SqlAlchemyUserRepository(db),
        reset_tokens=SqlAlchemyResetTokenRepository(db),
        tokens=SecureTokenGenerator(),
        frontend_url=get_settings().frontend_url,
        logo_base64=get_logo_base64(),
    )
    mail = await RequestPasswordReset(deps).execute(user_email, purpose=purpose)
    encolar_mail(background_tasks, mail)
