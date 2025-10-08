from typing import Optional, Dict, Any, List, TYPE_CHECKING

from aiogram.types import User as TelegramUser
from pydantic import BaseModel, field_validator

from config import settings

if TYPE_CHECKING:
    from .user_dto import UserDTO

class AuthDTO(BaseModel):
    platform: str = settings.platform
    social_id: str
    first_name: str = "Anonymous"
    last_name: str
    extra_data: Dict[str, Any] = {}
    nonce: Optional[str] = None

    class Config:
        _resource_name = "social-accounts"

    @field_validator("social_id", )
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{value.__name__} cannot be empty")
        return value

    @classmethod
    def from_telegram(cls, tlg_user: "TelegramUser") -> "AuthDTO":
        return cls(
            social_id=str(tlg_user.id),
            first_name=tlg_user.first_name,
            last_name=tlg_user.last_name or "",
            extra_data={
                "username": tlg_user.username,
                "language_code": tlg_user.language_code,
                "is_premium": tlg_user.is_premium,
                "added_to_attachment_menu": tlg_user.added_to_attachment_menu,
            },
        )


class AccountDTO(BaseModel):
    id: int
    platform: str
    social_id: str
    extra_data: Dict[str, Any] = {}
    user_id: str
    user: Optional["UserDTO"] = None

    class Config:
        _resource_name = "social-accounts"

    @field_validator("id", "social_id", "platform", "user_id")
    def validate_non_empty(cls, value: str, field):
        if not str(value).strip():
            raise ValueError(f"{field.name} cannot be empty")
        return value

    @classmethod
    def from_jsonapi(cls, acc: "ResourceObject", user: Optional["UserDTO"] = None) -> "AccountDTO":
        return cls(
            id=int(acc.id),
            platform=acc.platform,
            social_id=acc.social_id,
            extra_data=acc.extra_data,
            user_id=str(acc.user._resource_identifier.id),
            user=user
        )

class AuthResponseDTO(AccountDTO):
    created: bool = False
    nonce_status: Optional[str] = None