import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.auth.domain.entities.user import User


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    email: str
    full_name: str = Field(serialization_alias="fullName")
    is_active: bool = Field(serialization_alias="isActive")
    is_superadmin: bool = Field(serialization_alias="isSuperadmin")
    created_at: datetime = Field(serialization_alias="createdAt")
    color: str | None = None

    @classmethod
    def from_domain(cls, user: User) -> "AdminUserResponse":
        return cls(
            id=user.id,
            email=user.email.value,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superadmin=user.is_superadmin,
            created_at=user.created_at,
            color=user.color,
        )
