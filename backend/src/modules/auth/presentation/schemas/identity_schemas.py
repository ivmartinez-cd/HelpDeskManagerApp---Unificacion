import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.modules.auth.application.dtos.results import Identity


class UserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    email: str
    full_name: str = Field(serialization_alias="fullName")
    is_superadmin: bool = Field(serialization_alias="isSuperadmin")
    color: str | None = None


class PermissionResponse(BaseModel):
    module: str
    action: str


class IdentityResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user: UserResponse
    permissions: list[PermissionResponse]
    # Funciones (pantallas/cards) concedidas, por clave (ADR-032).
    features: list[str] = []

    @classmethod
    def from_domain(cls, identity: Identity) -> "IdentityResponse":
        user = UserResponse(
            id=identity.user.id,
            email=identity.user.email,
            full_name=identity.user.full_name,
            is_superadmin=identity.user.is_superadmin,
            color=identity.user.color,
        )
        permissions = [
            PermissionResponse(module=p.module, action=p.action) for p in identity.permissions
        ]
        return cls(user=user, permissions=permissions, features=sorted(identity.features))
