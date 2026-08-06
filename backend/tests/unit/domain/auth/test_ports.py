"""Los Protocols no tienen lógica que probar — esto solo confirma que los
puertos importan limpio (detecta typos/imports circulares antes de la
Etapa 6, cuando se escriben los adaptadores concretos)."""

from src.modules.auth.domain.repositories.login_attempt_repository import (
    LoginAttemptRepository,
)
from src.modules.auth.domain.repositories.permission_repository import PermissionRepository
from src.modules.auth.domain.repositories.reset_token_repository import ResetTokenRepository
from src.modules.auth.domain.repositories.session_repository import SessionRepository
from src.modules.auth.domain.repositories.user_repository import UserRepository
from src.modules.auth.domain.services.mailer import Mailer
from src.modules.auth.domain.services.password_hasher import PasswordHasher
from src.modules.auth.domain.services.scope_policy import ScopePolicy
from src.modules.auth.domain.services.session_token_generator import SessionTokenGenerator

_PORTS = (
    UserRepository,
    SessionRepository,
    PermissionRepository,
    ResetTokenRepository,
    LoginAttemptRepository,
    PasswordHasher,
    SessionTokenGenerator,
    Mailer,
    ScopePolicy,
)


def test_every_port_imports_as_a_protocol_class() -> None:
    for port in _PORTS:
        assert isinstance(port, type)
