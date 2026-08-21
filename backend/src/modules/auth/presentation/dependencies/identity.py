from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.application.use_cases.get_current_identity import (
    GetCurrentIdentity,
    GetCurrentIdentityDependencies,
)
from src.modules.auth.domain.errors import NotAuthenticatedError
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
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_db


async def get_current_identity(
    request: Request, db: AsyncSession = Depends(get_db, scope="function")
) -> Identity:
    token = request.cookies.get(get_settings().session_cookie_name)
    if not token:
        raise NotAuthenticatedError()
    deps = GetCurrentIdentityDependencies(
        sessions=SqlAlchemySessionRepository(db),
        users=SqlAlchemyUserRepository(db),
        permissions=SqlAlchemyPermissionRepository(db),
        tokens=SecureTokenGenerator(),
    )
    return await GetCurrentIdentity(deps).execute(token)
