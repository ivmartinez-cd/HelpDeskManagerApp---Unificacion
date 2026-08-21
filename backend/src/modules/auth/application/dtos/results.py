import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PermissionView:
    module: str
    action: str


@dataclass(frozen=True, slots=True)
class UserView:
    id: uuid.UUID
    email: str
    full_name: str
    is_superadmin: bool
    color: str | None


@dataclass(frozen=True, slots=True)
class Identity:
    """`session_id` no se expone en ningún response JSON (ver
    IdentityResponse) — existe para que change-password pueda revocar
    "las demás" sesiones sin tocar la que originó el request."""

    user: UserView
    permissions: frozenset[PermissionView]
    session_id: uuid.UUID
    # Funciones (pantallas/cards) concedidas, por clave (ADR-032). Vacío para
    # quien no tiene ninguna; el superadmin se resuelve en `require_feature`.
    features: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    """`session_token` es el token en crudo — solo existe en memoria durante
    este request; lo único que se persiste es su hash."""

    identity: Identity
    session_token: str
